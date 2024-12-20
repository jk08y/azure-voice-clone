# main.py
from src.azure_voice_client import AzureVoiceClient
from src.audio_preprocessing import AudioPreprocessor
from src.dataset_preparation import DatasetPreparation
from pathlib import Path
import os

def main():
    # Initialize components
    audio_preprocessor = AudioPreprocessor()
    dataset_prep = DatasetPreparation(
        audio_dir="data/audio_samples",
        transcript_dir="data/transcripts"
    )
    azure_client = AzureVoiceClient()
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Step 1: Process and validate audio files
    print("Processing audio files...")
    for audio_file in Path("data/audio_samples").glob("*.wav"):
        valid, requirements = audio_preprocessor.validate_audio_file(audio_file)
        if not valid:
            print(f"Processing {audio_file}...")
            audio_preprocessor.process_audio(audio_file)
    
    # Step 2: Prepare dataset
    print("Preparing dataset...")
    dataset_file = dataset_prep.export_dataset("output/dataset.json")
    
    # Step 3: Create custom voice model
    print("Creating custom voice model...")
    azure_client.create_custom_voice("MyCustomVoice", dataset_file)
    
    # Step 4: Test synthesis
    print("Testing speech synthesis...")
    test_text = "Hello, this is a test of the custom voice synthesis system."
    success = azure_client.synthesize_speech(
        text=test_text,
        output_file="output/test_synthesis.wav",
        voice_name="en-US-JennyNeural"  # Replace with your custom voice name once created
    )
    
    if success:
        print("Speech synthesis completed successfully!")
    else:
        print("Speech synthesis failed. Please check the error messages above.")

if __name__ == "__main__":
    main()