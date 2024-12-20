import soundfile as sf
import numpy as np
import os
from pathlib import Path

class AudioPreprocessor:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.min_duration = 0.5
        self.max_duration = 15
        
    def validate_audio_file(self, file_path):
        """Validate if audio file meets Azure's requirements."""
        try:
            data, samplerate = sf.read(file_path)
            duration = len(data) / samplerate
            
            requirements = {
                "sample_rate": samplerate == self.sample_rate,
                "duration": self.min_duration <= duration <= self.max_duration,
                "channels": len(data.shape) == 1 or data.shape[1] == 1,
                "file_size": os.path.getsize(file_path) < 1024 * 1024 * 100  # 100MB limit
            }
            
            return all(requirements.values()), requirements
        except Exception as e:
            return False, str(e)
    
    def process_audio(self, input_file, output_file=None):
        """Process audio file to meet Azure's requirements."""
        data, samplerate = sf.read(input_file)
        
        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Resample if necessary
        if samplerate != self.sample_rate:
            # Note: You might want to use a more sophisticated resampling method
            samples = int(len(data) * self.sample_rate / samplerate)
            data = np.interp(
                np.linspace(0, len(data), samples),
                np.arange(len(data)),
                data
            )
        
        # Normalize audio
        data = data / np.max(np.abs(data))
        
        # Save processed audio
        output_file = output_file or input_file
        sf.write(output_file, data, self.sample_rate)
        return output_file