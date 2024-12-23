import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import AzureError, ResourceExistsError
from config.azure_config import AzureConfig
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Union
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from dataclasses import dataclass
import aiofiles
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VoiceModel:
    """Data class for voice model information."""
    model_id: str
    name: str
    status: str
    created_date: datetime
    last_modified: datetime

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass

class AzureVoiceClient:
    """Enhanced Azure Voice Client with advanced features and better error handling."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Azure Voice Client.
        
        Args:
            config_path: Optional path to configuration file
        """
        self._initialize_config(config_path)
        self._setup_clients()
        self._lock = threading.Lock()
        self.cache = {}
        
    def _initialize_config(self, config_path: Optional[str]) -> None:
        """Initialize configuration with optional custom config file."""
        if config_path:
            AzureConfig.load_from_file(config_path)
        AzureConfig.validate_config()
        
    def _setup_clients(self) -> None:
        """Set up Azure clients with retry policies and connection pooling."""
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=AzureConfig.SPEECH_KEY,
                region=AzureConfig.SPEECH_REGION
            )
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_LogFilename,
                "speech_log.txt"
            )
            
            self.blob_service_client = BlobServiceClient.from_connection_string(
                AzureConfig.STORAGE_CONNECTION_STRING,
                connection_timeout=30,
                read_timeout=120
            )
            
            self.container_client = self.blob_service_client.get_container_client(
                AzureConfig.CONTAINER_NAME
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure clients: {str(e)}")
            raise
            
    async def upload_training_data(self, dataset_file: str, max_workers: int = 4) -> bool:
        """
        Asynchronously upload training data to Azure Blob Storage with parallel processing.
        
        Args:
            dataset_file: Path to the dataset file
            max_workers: Maximum number of parallel upload workers
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure container exists
            await self._ensure_container_exists()
            
            # Load and validate dataset
            dataset = await self._load_and_validate_dataset(dataset_file)
            
            # Calculate total size and validate storage quota
            total_size = await self._calculate_total_size(dataset)
            await self._validate_storage_quota(total_size)
            
            # Upload dataset file with metadata
            await self._upload_dataset_file(dataset_file)
            
            # Upload audio files in parallel
            async with asyncio.Semaphore(max_workers):
                upload_tasks = [
                    self._upload_audio_file(item['audio_file'])
                    for item in dataset
                ]
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                
            # Check for any upload failures
            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                logger.error(f"Failed to upload {len(failures)} files")
                raise AudioProcessingError(f"Upload failed for some files: {failures}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload training data: {str(e)}")
            raise
            
    async def create_custom_voice(
        self,
        model_name: str,
        dataset_file: str,
        description: Optional[str] = None,
        locale: str = "en-US"
    ) -> VoiceModel:
        """
        Create a custom voice model with enhanced monitoring and validation.
        
        Args:
            model_name: Name of the custom voice model
            dataset_file: Path to the dataset file
            description: Optional description of the model
            locale: Voice model locale
            
        Returns:
            VoiceModel: Created voice model information
        """
        try:
            # Upload training data if needed
            await self.upload_training_data(dataset_file)
            
            # Validate model name and parameters
            self._validate_model_parameters(model_name, locale)
            
            # Create custom voice model
            model_response = await self._create_voice_model(
                model_name,
                dataset_file,
                description,
                locale
            )
            
            # Monitor training progress
            model_info = await self._monitor_training_progress(model_response['id'])
            
            return VoiceModel(
                model_id=model_info['id'],
                name=model_name,
                status=model_info['status'],
                created_date=datetime.fromisoformat(model_info['created_date']),
                last_modified=datetime.fromisoformat(model_info['last_modified'])
            )
            
        except Exception as e:
            logger.error(f"Failed to create custom voice: {str(e)}")
            raise
            
    async def synthesize_speech(
        self,
        text: str,
        output_file: str,
        voice_name: Optional[str] = None,
        pitch: int = 0,
        rate: int = 0,
        volume: int = 100
    ) -> bool:
        """
        Synthesize speech with enhanced control and streaming capabilities.
        
        Args:
            text: Text to synthesize
            output_file: Output audio file path
            voice_name: Optional custom voice name
            pitch: Voice pitch adjustment (-50 to 50)
            rate: Speech rate adjustment (-50 to 50)
            volume: Volume level (0 to 100)
            
        Returns:
            bool: Success status
        """
        try:
            # Configure synthesis parameters
            self._configure_synthesis_params(voice_name, pitch, rate, volume)
            
            # Create output directory if needed
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate speech with progress monitoring
            async with aiofiles.open(output_file, 'wb') as f:
                result = await self._generate_speech_with_progress(text, f)
                
            # Validate output
            if not await self._validate_audio_output(output_file):
                raise AudioProcessingError("Generated audio file is invalid")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {str(e)}")
            raise
            
    async def _ensure_container_exists(self) -> None:
        """Ensure blob container exists with proper configuration."""
        try:
            await self.container_client.create_container(
                metadata={'purpose': 'voice-training'},
                public_access='blob'
            )
        except ResourceExistsError:
            pass
            
    async def _load_and_validate_dataset(self, dataset_file: str) -> List[Dict]:
        """Load and validate dataset file."""
        async with aiofiles.open(dataset_file, 'r') as f:
            content = await f.read()
            dataset = json.loads(content)
            
        if not self._validate_dataset_format(dataset):
            raise ValueError("Invalid dataset format")
            
        return dataset
        
    def _validate_dataset_format(self, dataset: List[Dict]) -> bool:
        """Validate dataset format and required fields."""
        required_fields = {'audio_file', 'text', 'duration'}
        return all(
            all(field in item for field in required_fields)
            for item in dataset
        )
        
    async def _calculate_total_size(self, dataset: List[Dict]) -> int:
        """Calculate total size of audio files."""
        total_size = 0
        for item in dataset:
            file_path = Path(item['audio_file'])
            if file_path.exists():
                total_size += file_path.stat().st_size
        return total_size
        
    async def _validate_storage_quota(self, total_size: int) -> None:
        """Validate storage quota and available space."""
        # Implement quota validation logic here
        pass
        
    async def _upload_audio_file(self, audio_path: str) -> None:
        """Upload single audio file with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                audio_path = Path(audio_path)
                blob_name = f"audio/{audio_path.name}"
                
                # Calculate file hash for integrity check
                file_hash = await self._calculate_file_hash(audio_path)
                
                async with aiofiles.open(audio_path, 'rb') as audio_data:
                    blob_client = self.container_client.get_blob_client(blob_name)
                    content = await audio_data.read()
                    
                    await blob_client.upload_blob(
                        content,
                        overwrite=True,
                        metadata={'file_hash': file_hash}
                    )
                    
                # Verify upload
                if not await self._verify_upload(blob_client, file_hash):
                    raise AudioProcessingError("Upload verification failed")
                    
                return
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (2 ** attempt))
                
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
        
    async def _verify_upload(self, blob_client: BlobClient, file_hash: str) -> bool:
        """Verify uploaded file integrity."""
        properties = await blob_client.get_blob_properties()
        return properties.metadata.get('file_hash') == file_hash
        
    async def _monitor_training_progress(self, model_id: str) -> Dict:
        """Monitor custom voice model training progress."""
        while True:
            status = await self._get_model_status(model_id)
            if status['status'] in {'Succeeded', 'Failed'}:
                return status
            await asyncio.sleep(60)
            
    async def _get_model_status(self, model_id: str) -> Dict:
        """Get current status of voice model."""
        # Implement status check logic here
        pass
        
    def __enter__(self):
        """Context manager enter."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.speech_config = None
        if hasattr(self, 'blob_service_client'):
            self.blob_service_client.close()
