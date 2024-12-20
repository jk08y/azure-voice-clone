import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient
from config.azure_config import AzureConfig
import json
from pathlib import Path

class AzureVoiceClient:
    def __init__(self):
        AzureConfig.validate_config()
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AzureConfig.SPEECH_KEY,
            region=AzureConfig.SPEECH_REGION
        )
        self.blob_service_client = BlobServiceClient.from_connection_string(
            AzureConfig.STORAGE_CONNECTION_STRING
        )
        
    def upload_training_data(self, dataset_file: str):
        """Upload training data to Azure Blob Storage."""
        container_client = self.blob_service_client.get_container_client(
            AzureConfig.CONTAINER_NAME
        )
        
        # Create container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
        
        # Upload dataset file
        with open(dataset_file, 'rb') as data:
            blob_client = container_client.get_blob_client(Path(dataset_file).name)
            blob_client.upload_blob(data, overwrite=True)
        
        # Upload audio files
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
            
        for item in dataset:
            audio_path = item['audio_file']
            blob_name = f"audio/{Path(audio_path).name}"
            
            with open(audio_path, 'rb') as audio_data:
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(audio_data, overwrite=True)
        
        return True
    
    def create_custom_voice(self, model_name: str, dataset_file: str):
        """Create custom voice model using Azure Custom Neural Voice."""
        # Upload training data
        self.upload_training_data(dataset_file)
        
        # Note: This is a placeholder for the actual Custom Neural Voice API call
        # Azure's Custom Neural Voice requires special access and approval
        print(f"Creating custom voice model: {model_name}")
        print("Note: Custom Neural Voice requires approved access from Azure.")
        
    def synthesize_speech(self, text: str, output_file: str, voice_name: str = None):
        """Synthesize speech from text using either default or custom voice."""
        if voice_name:
            self.speech_config.speech_synthesis_voice_name = voice_name
        
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(result)
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            print(f"Error details: {cancellation_details.error_details}")
            return False
        else:
            print(f"Error: {result.reason}")
            return False