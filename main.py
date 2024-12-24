import logging
from pathlib import Path
import os
import json
import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import yaml

from src.azure_voice_client import AzureVoiceClient
from src.audio_preprocessing import AudioPreprocessor
from src.dataset_preparation import DatasetPreparation

@dataclass
class Config:
    audio_dir: str
    transcript_dir: str
    output_dir: str
    log_file: str
    supported_formats: list
    min_sample_rate: int
    max_file_size_mb: int
    default_voice: str

class VoiceSynthesisSystem:
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.audio_preprocessor = AudioPreprocessor()
        self.dataset_prep = DatasetPreparation(
            audio_dir=self.config.audio_dir,
            transcript_dir=self.config.transcript_dir
        )
        self.azure_client = AzureVoiceClient()
        
        # Create necessary directories
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)

    def _load_config(self, config_path: str) -> Config:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return Config(**config_data)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Fallback to default configuration
            return Config(
                audio_dir="data/audio_samples",
                transcript_dir="data/transcripts",
                output_dir="output",
                log_file="logs/voice_synthesis.log",
                supported_formats=[".wav", ".mp3"],
                min_sample_rate=16000,
                max_file_size_mb=100,
                default_voice="en-US-JennyNeural"
            )

    def _setup_logging(self):
        """Configure logging settings."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def process_audio_files(self) -> Dict[str, bool]:
        """Process and validate all audio files in the input directory."""
        results = {}
        self.logger.info("Starting audio file processing...")
        
        try:
            for audio_format in self.config.supported_formats:
                for audio_file in Path(self.config.audio_dir).glob(f"*{audio_format}"):
                    try:
                        valid, requirements = self.audio_preprocessor.validate_audio_file(audio_file)
                        if not valid:
                            self.logger.info(f"Processing {audio_file}...")
                            success = self.audio_preprocessor.process_audio(audio_file)
                            results[str(audio_file)] = success
                        else:
                            results[str(audio_file)] = True
                    except Exception as e:
                        self.logger.error(f"Error processing {audio_file}: {e}")
                        results[str(audio_file)] = False
        except Exception as e:
            self.logger.error(f"Error during audio processing: {e}")
        
        return results

    def prepare_dataset(self, output_name: str = "dataset.json") -> Optional[Path]:
        """Prepare and export the dataset."""
        try:
            self.logger.info("Preparing dataset...")
            output_path = Path(self.config.output_dir) / output_name
            dataset_file = self.dataset_prep.export_dataset(str(output_path))
            self.logger.info(f"Dataset exported to {output_path}")
            return dataset_file
        except Exception as e:
            self.logger.error(f"Error preparing dataset: {e}")
            return None

    def create_voice_model(self, model_name: str, dataset_file: Path) -> bool:
        """Create a custom voice model."""
        try:
            self.logger.info(f"Creating custom voice model: {model_name}")
            success = self.azure_client.create_custom_voice(model_name, dataset_file)
            if success:
                self.logger.info("Custom voice model created successfully")
            else:
                self.logger.error("Failed to create custom voice model")
            return success
        except Exception as e:
            self.logger.error(f"Error creating voice model: {e}")
            return False

    def synthesize_text(
        self,
        text: str,
        output_file: Optional[str] = None,
        voice_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Synthesize speech from text."""
        try:
            voice_name = voice_name or self.config.default_voice
            if output_file is None:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_file = f"{self.config.output_dir}/synthesis_{timestamp}.wav"
            
            self.logger.info(f"Synthesizing speech using voice: {voice_name}")
            success = self.azure_client.synthesize_speech(
                text=text,
                output_file=output_file,
                voice_name=voice_name
            )
            
            if success:
                self.logger.info(f"Speech synthesis completed: {output_file}")
                return True, output_file
            else:
                self.logger.error("Speech synthesis failed")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")
            return False, None

def main():
    # Initialize the system
    system = VoiceSynthesisSystem()
    
    # Process audio files
    processing_results = system.process_audio_files()
    
    # Prepare dataset
    dataset_file = system.prepare_dataset()
    if not dataset_file:
        print("Failed to prepare dataset. Exiting...")
        return
    
    # Create custom voice model
    model_name = "MyCustomVoice"
    if not system.create_voice_model(model_name, dataset_file):
        print("Failed to create voice model. Exiting...")
        return
    
    # Test synthesis
    test_text = "Hello, this is a test of the custom voice synthesis system."
    success, output_file = system.synthesize_text(test_text)
    
    if success:
        print(f"Speech synthesis completed successfully! Output file: {output_file}")
    else:
        print("Speech synthesis failed. Please check the logs for details.")

if __name__ == "__main__":
    main()
