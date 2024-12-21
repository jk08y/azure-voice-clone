import pandas as pd
from pathlib import Path
import json
from typing import List, Dict

class DatasetPreparation:
    def __init__(self, audio_dir: str, transcript_dir: str):
        self.audio_dir = Path(audio_dir)
        self.transcript_dir = Path(transcript_dir)
        
    def create_training_dataset(self) -> List[Dict]:
        """Create dataset for Azure Custom Voice training."""
        dataset = []
        
        # Get all audio files

        audio_files = list(self.audio_dir.glob("*.wav"))
        
        for audio_file in audio_files:
            transcript_file = self.transcript_dir / f"{audio_file.stem}.txt"
            
            if not transcript_file.exists():
                print(f"Warning: No transcript found for {audio_file}")
                continue
                
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            
            dataset.append({
                "audio_file": str(audio_file),
                "transcript": transcript,
                "duration": self._get_audio_duration(audio_file)
            })
        
        return dataset
    
    def export_dataset(self, output_file: str):
        """Export dataset to JSON format."""
        dataset = self.create_training_dataset()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"Dataset exported to {output_file}")
        return output_file
    
    def _get_audio_duration(self, audio_file: Path) -> float:
        """Get duration of audio file in seconds."""
        import soundfile as sf
        with sf.SoundFile(audio_file) as f:
            return len(f) / f.samplerate