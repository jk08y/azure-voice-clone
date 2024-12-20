from dotenv import load_dotenv
import os

load_dotenv()

class AzureConfig:
    SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
    SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
    STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    CONTAINER_NAME = os.getenv('AZURE_CONTAINER_NAME', 'voice-samples')
    
    @classmethod
    def validate_config(cls):
        required_vars = ['SPEECH_KEY', 'SPEECH_REGION', 'STORAGE_CONNECTION_STRING']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return True
