# Azure Voice Cloning

A voice cloning built with Azure Custom Neural Voice, allowing you to create a digital version of your voice for content creation and YouTube tutorials.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Azure Speech SDK](https://img.shields.io/badge/Azure-Speech%20SDK-0078D4.svg)](https://docs.microsoft.com/azure/cognitive-services/speech-service/)

## Features

- High-quality voice cloning using Azure Custom Neural Voice
- Automatic audio validation and preprocessing
- Dataset preparation for model training
- Azure integration for model training and synthesis
- Batch processing capabilities
- Audio quality validation

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher installed
- An Azure account with Speech Services enabled
- Approved access to Azure Custom Neural Voice
- 30-50 high-quality voice recordings (0.5-15 seconds each)
- Transcripts for each recording

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jk08y/azure-voice-clone.git
cd azure-voice-clone
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```env
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=your_region_here
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
```

4. Create required directories:
```bash
mkdir -p data/audio_samples data/transcripts output
```

## Project Structure

```
azure_voice_project/
│
├── config/
│   └── azure_config.py          # Azure credentials and configuration
│
├── data/
│   ├── audio_samples/           # Your voice recordings
│   └── transcripts/             # Transcripts for recordings
│
├── src/
│   ├── audio_preprocessing.py   # Audio processing utilities
│   ├── azure_voice_client.py    # Azure Custom Voice API client
│   ├── dataset_preparation.py   # Dataset preparation tools
│   └── text_to_speech.py        # Text-to-speech conversion
│
├── requirements.txt
└── main.py
```

## Usage

1. Place your WAV audio recordings in `data/audio_samples/`

2. Add corresponding transcripts in `data/transcripts/`:
   - Each transcript should be a `.txt` file
   - Name should match the audio file (e.g., `recording1.wav` → `recording1.txt`)

3. Run the system:
```bash
python3 main.py
```

The system will:
- Validate and process your audio files
- Prepare the training dataset
- Upload data to Azure
- Create your custom voice model
- Test the synthesis

## Audio Requirements

- Format: WAV
- Sample rate: 44.1 kHz
- Duration: 0.5-15 seconds per recording
- Quality: Clear audio, minimal background noise
- Total recordings: 30-50 samples recommended

## API Reference

### AudioPreprocessor

```python
preprocessor = AudioPreprocessor()
valid, requirements = preprocessor.validate_audio_file("audio.wav")
processed_file = preprocessor.process_audio("input.wav", "output.wav")
```

### AzureVoiceClient

```python
client = AzureVoiceClient()
client.create_custom_voice("MyVoice", "dataset.json")
client.synthesize_speech("Hello world", "output.wav", "MyCustomVoice")
```

## Common Issues

1. **Audio Validation Fails**
   - Ensure audio meets the requirements above
   - Check for background noise
   - Verify file format and sample rate

2. **Azure Authentication Errors**
   - Verify credentials in `.env` file
   - Check Azure subscription status
   - Ensure Speech Services are enabled

3. **Model Training Issues**
   - Verify Custom Neural Voice access
   - Check dataset format
   - Ensure sufficient training samples

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Azure Cognitive Services team for the Speech SDK
- Contributors and testers
- Open source community

## Contact

Your Name - [@jk08y](https://github.com/jk08y)

Project Link: [https://github.com/jk08y/azure-voice-clone](https://github.com/jk08y/azure-voice-clone)

## Support

⭐️ If you find this project helpful, please consider giving it a star!