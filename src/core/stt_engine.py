"""
Speech-to-Text Engine with Industrial Noise Reduction
Optimized for factory floor, warehouse, and field environments
"""

import whisper
import noisereduce as nr
import numpy as np
import soundfile as sf
import torch
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class IndustrialSTT:
    """Speech recognition optimized for noisy industrial environments"""
    
    def __init__(
        self,
        model_size: str = "medium.en",
        device: str = "auto",
        noise_reduction_enabled: bool = True,
        sample_rate: int = 16000
    ):
        """
        Initialize STT engine
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device for inference (auto, cpu, cuda)
            noise_reduction_enabled: Enable noise reduction preprocessing
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.noise_reduction_enabled = noise_reduction_enabled
        
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Loading Whisper model: {model_size} on {self.device}")
        self.model = whisper.load_model(model_size, device=self.device)
        
        # Noise profile for stationary noise reduction
        self.noise_profile = None
        
        # Industrial vocabulary hints
        self.domain_vocabulary = [
            "SKU", "pallet", "forklift", "warehouse", "inventory",
            "stock", "location", "work order", "bin", "rack"
        ]
        
    def calibrate_noise(self, audio_file: str, duration: float = 2.0):
        """
        Calibrate noise profile from ambient recording
        
        Args:
            audio_file: Path to ambient noise recording
            duration: Duration to sample in seconds
        """
        logger.info(f"Calibrating noise profile from {audio_file}")
        audio_data, sr = sf.read(audio_file)
        
        # Resample if needed
        if sr != self.sample_rate:
            audio_data = self._resample(audio_data, sr, self.sample_rate)
        
        # Store noise profile
        self.noise_profile = audio_data[:int(duration * self.sample_rate)]
        logger.info("Noise calibration complete")
        
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction and preprocessing
        
        Args:
            audio_data: Raw audio numpy array
            
        Returns:
            Preprocessed audio
        """
        if not self.noise_reduction_enabled:
            return audio_data
            
        logger.debug("Applying noise reduction")
        
        # Reduce stationary noise (factory background)
        reduced_noise = nr.reduce_noise(
            y=audio_data,
            sr=self.sample_rate,
            stationary=True,
            prop_decrease=0.8,  # Aggressive reduction for industrial noise
            freq_mask_smooth_hz=500,
            time_mask_smooth_ms=50
        )
        
        # Normalize audio levels
        max_val = np.max(np.abs(reduced_noise))
        if max_val > 0:
            reduced_noise = reduced_noise / max_val * 0.9
            
        return reduced_noise
    
    def transcribe(
        self,
        audio_file: str,
        language: str = "en",
        initial_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file: Path to audio file
            language: Language code
            initial_prompt: Context hint for better accuracy
            
        Returns:
            Dictionary with 'text', 'confidence', 'segments'
        """
        logger.info(f"Transcribing: {audio_file}")
        
        # Load audio
        audio_data, sr = sf.read(audio_file)
        
        # Resample if needed
        if sr != self.sample_rate:
            audio_data = self._resample(audio_data, sr, self.sample_rate)
        
        # Preprocess
        audio_data = self.preprocess_audio(audio_data)
        
        # Prepare initial prompt with domain vocabulary
        if initial_prompt is None:
            initial_prompt = ", ".join(self.domain_vocabulary)
            
        # Transcribe
        result = self.model.transcribe(
            audio_data,
            language=language,
            initial_prompt=initial_prompt,
            temperature=0.2,  # Lower temperature for consistency
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(result)
        
        logger.info(f"Transcription: '{result['text']}' (confidence: {confidence:.2f})")
        
        return {
            "text": result["text"].strip(),
            "confidence": confidence,
            "segments": result.get("segments", []),
            "language": result.get("language", language)
        }
    
    def transcribe_realtime(
        self,
        audio_chunk: np.ndarray,
        context: Optional[str] = None
    ) -> str:
        """
        Transcribe audio chunk in real-time streaming mode
        
        Args:
            audio_chunk: Audio data chunk
            context: Previous transcription context
            
        Returns:
            Transcribed text
        """
        # Preprocess chunk
        processed = self.preprocess_audio(audio_chunk)
        
        # Transcribe
        result = self.model.transcribe(
            processed,
            language="en",
            initial_prompt=context or ", ".join(self.domain_vocabulary),
            temperature=0.0
        )
        
        return result["text"].strip()
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate average confidence from segment log probabilities"""
        if "segments" not in result or not result["segments"]:
            return 0.0
            
        total_logprob = 0.0
        total_tokens = 0
        
        for segment in result["segments"]:
            if "avg_logprob" in segment:
                tokens = segment.get("tokens", [])
                total_logprob += segment["avg_logprob"] * len(tokens)
                total_tokens += len(tokens)
        
        if total_tokens == 0:
            return 0.0
            
        avg_logprob = total_logprob / total_tokens
        # Convert log probability to confidence (0-1 scale)
        confidence = np.exp(avg_logprob)
        
        return min(confidence, 1.0)
    
    def _resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """Resample audio to target sample rate"""
        from scipy import signal
        
        num_samples = int(len(audio) * target_sr / orig_sr)
        resampled = signal.resample(audio, num_samples)
        return resampled


if __name__ == "__main__":
    # Test the STT engine
    stt = IndustrialSTT(model_size="base.en")
    
    # Example usage
    print("Industrial STT Engine initialized")
    print(f"Device: {stt.device}")
    print(f"Sample rate: {stt.sample_rate} Hz")
