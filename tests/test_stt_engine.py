"""
Unit tests for STT Engine
"""

import pytest
import numpy as np
from pathlib import Path
import soundfile as sf

from src.core.stt_engine import IndustrialSTT


class TestIndustrialSTT:
    """Test cases for STT engine"""
    
    @pytest.fixture
    def stt_engine(self):
        """Create STT engine for testing"""
        return IndustrialSTT(model_size="base.en", device="cpu")
    
    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create sample audio file"""
        # Generate simple sine wave
        sample_rate = 16000
        duration = 2.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Save to file
        audio_file = tmp_path / "test_audio.wav"
        sf.write(audio_file, audio, sample_rate)
        
        return str(audio_file)
    
    def test_initialization(self, stt_engine):
        """Test STT engine initialization"""
        assert stt_engine is not None
        assert stt_engine.model is not None
        assert stt_engine.sample_rate == 16000
        assert stt_engine.noise_reduction_enabled is True
    
    def test_preprocess_audio(self, stt_engine):
        """Test audio preprocessing"""
        # Generate noisy audio
        audio = np.random.randn(16000)
        
        # Preprocess
        processed = stt_engine.preprocess_audio(audio)
        
        assert processed is not None
        assert len(processed) == len(audio)
        assert isinstance(processed, np.ndarray)
    
    def test_transcribe(self, stt_engine, sample_audio):
        """Test audio transcription"""
        result = stt_engine.transcribe(sample_audio)
        
        assert "text" in result
        assert "confidence" in result
        assert "segments" in result
        assert isinstance(result["text"], str)
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_confidence_calculation(self, stt_engine):
        """Test confidence score calculation"""
        # Mock result with segments
        result = {
            "segments": [
                {"avg_logprob": -0.5, "tokens": [1, 2, 3]},
                {"avg_logprob": -0.3, "tokens": [4, 5]}
            ]
        }
        
        confidence = stt_engine._calculate_confidence(result)
        
        assert 0.0 <= confidence <= 1.0
    
    def test_noise_reduction_disabled(self, tmp_path):
        """Test with noise reduction disabled"""
        stt = IndustrialSTT(noise_reduction_enabled=False)
        
        # Generate test audio
        audio = np.random.randn(16000)
        processed = stt.preprocess_audio(audio)
        
        # Should return original audio
        np.testing.assert_array_equal(processed, audio)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
