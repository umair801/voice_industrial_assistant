"""
Text-to-Speech Engine
Generates voice responses for industrial assistant
"""

import pyttsx3
from typing import Optional
import threading
import queue
import logging

logger = logging.getLogger(__name__)


class IndustrialTTS:
    """Text-to-speech engine optimized for industrial environments"""
    
    def __init__(
        self,
        rate: int = 150,
        volume: float = 1.0,
        voice_id: Optional[str] = None
    ):
        """
        Initialize TTS engine
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID to use
        """
        self.engine = pyttsx3.init()
        
        # Set properties
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Set voice if specified
        if voice_id:
            self.engine.setProperty('voice', voice_id)
        else:
            # Use first available voice
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        
        # Message queue for async speaking
        self.message_queue = queue.Queue()
        self.speaking = False
        
        # Start background thread for TTS
        self.tts_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.tts_thread.start()
        
        logger.info("TTS engine initialized")
    
    def speak(self, text: str, blocking: bool = False):
        """
        Speak text
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
        """
        if not text:
            return
        
        logger.debug(f"Speaking: '{text}'")
        
        if blocking:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            # Add to queue for async processing
            self.message_queue.put(text)
    
    def _process_queue(self):
        """Background thread to process TTS queue"""
        while True:
            try:
                text = self.message_queue.get(timeout=1)
                self.speaking = True
                
                self.engine.say(text)
                self.engine.runAndWait()
                
                self.speaking = False
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS error: {e}")
                self.speaking = False
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.speaking or not self.message_queue.empty()
    
    def stop(self):
        """Stop current speech"""
        self.engine.stop()
        
        # Clear queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                break
        
        self.speaking = False
    
    def set_rate(self, rate: int):
        """Set speech rate"""
        self.engine.setProperty('rate', rate)
        logger.info(f"Speech rate set to {rate} WPM")
    
    def set_volume(self, volume: float):
        """Set volume level"""
        self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
        logger.info(f"Volume set to {volume}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        voices = self.engine.getProperty('voices')
        return [{"id": v.id, "name": v.name, "languages": v.languages} for v in voices]
    
    def set_voice(self, voice_id: str):
        """Set voice by ID"""
        self.engine.setProperty('voice', voice_id)
        logger.info(f"Voice set to {voice_id}")


if __name__ == "__main__":
    # Test TTS engine
    tts = IndustrialTTS()
    
    print("Available voices:")
    for voice in tts.get_available_voices():
        print(f"  - {voice['name']} ({voice['id']})")
    
    print("\nTesting speech...")
    tts.speak("Voice assistant ready for industrial operations", blocking=True)
    print("Done")
