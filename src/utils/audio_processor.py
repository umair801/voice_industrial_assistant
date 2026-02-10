"""
Audio Processing Utilities
Handles audio recording and preprocessing
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Records audio from microphone"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device_id: int = None,
        silence_threshold: float = 0.01,
        silence_duration: float = 2.0
    ):
        """
        Initialize audio recorder
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            device_id: Specific device ID (None for default)
            silence_threshold: RMS threshold for silence detection
            silence_duration: Seconds of silence before stopping
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id = device_id
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        
        # Output directory
        self.output_dir = Path(tempfile.gettempdir()) / "voice_assistant"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Audio recorder initialized (device: {device_id})")
    
    def record_command(
        self,
        max_duration: float = 10.0
    ) -> str:
        """
        Record voice command with automatic silence detection
        
        Args:
            max_duration: Maximum recording duration in seconds
            
        Returns:
            Path to recorded audio file
        """
        logger.info("Recording command...")
        
        # Recording buffer
        recording = []
        silence_samples = int(self.silence_duration * self.sample_rate)
        max_samples = int(max_duration * self.sample_rate)
        
        def callback(indata, frames, time, status):
            """Audio stream callback"""
            if status:
                logger.warning(f"Audio status: {status}")
            
            recording.append(indata.copy())
        
        # Start recording
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device_id,
            callback=callback
        ):
            # Record until silence or max duration
            while len(recording) * 1024 < max_samples:
                sd.sleep(100)
                
                # Check for silence
                if len(recording) > 0:
                    recent_audio = np.concatenate(recording[-10:])
                    rms = np.sqrt(np.mean(recent_audio**2))
                    
                    if rms < self.silence_threshold:
                        # Found silence
                        if len(recording) * 1024 > silence_samples:
                            break
        
        # Convert to numpy array
        audio_data = np.concatenate(recording, axis=0)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"command_{timestamp}.wav"
        
        sf.write(output_file, audio_data, self.sample_rate)
        
        logger.info(f"Recorded {len(audio_data)/self.sample_rate:.2f}s to {output_file}")
        
        return str(output_file)
    
    def record_fixed_duration(self, duration: float = 3.0) -> str:
        """
        Record for fixed duration
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to recorded audio file
        """
        logger.info(f"Recording for {duration}s...")
        
        # Record
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device_id
        )
        sd.wait()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"fixed_{timestamp}.wav"
        
        sf.write(output_file, audio_data, self.sample_rate)
        
        logger.info(f"Recorded to {output_file}")
        
        return str(output_file)
    
    def list_devices(self):
        """List available audio devices"""
        devices = sd.query_devices()
        
        print("\nAvailable Audio Devices:")
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']} "
                  f"(in: {device['max_input_channels']}, "
                  f"out: {device['max_output_channels']})")
        
        return devices


if __name__ == "__main__":
    # Test audio recorder
    recorder = AudioRecorder()
    
    # List devices
    recorder.list_devices()
    
    # Test recording
    print("\nPress Enter to start recording...")
    input()
    
    audio_file = recorder.record_fixed_duration(3.0)
    print(f"Saved to: {audio_file}")
