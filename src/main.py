"""
Voice-Activated Industrial Assistant
Main application entry point
"""

import yaml
import logging
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

from core.stt_engine import IndustrialSTT
from core.nlu_engine import IndustrialNLU, Intent
from core.dialogue_manager import DialogueManager
from core.tts_engine import IndustrialTTS
from integrations.erp_connector import ERPConnector
from integrations.wms_connector import WMSConnector
from utils.audio_processor import AudioRecorder
from utils.logger import setup_logging
from utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class VoiceIndustrialAssistant:
    """Main voice assistant application"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize voice assistant
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        setup_logging(
            log_level=self.config.get("logging", {}).get("level", "INFO"),
            log_file=self.config.get("logging", {}).get("file")
        )
        
        logger.info("Initializing Voice Industrial Assistant")
        
        # Initialize components
        self._init_stt()
        self._init_nlu()
        self._init_tts()
        self._init_dialogue_manager()
        self._init_integrations()
        self._init_audio_recorder()
        
        # Metrics
        self.metrics = MetricsCollector()
        
        # Register action handlers
        self._register_handlers()
        
        logger.info("Voice Industrial Assistant initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _init_stt(self):
        """Initialize speech-to-text engine"""
        stt_config = self.config.get("stt", {})
        
        self.stt = IndustrialSTT(
            model_size=stt_config.get("model", "medium.en"),
            device=stt_config.get("device", "auto"),
            noise_reduction_enabled=stt_config.get("noise_reduction", True),
            sample_rate=stt_config.get("sample_rate", 16000)
        )
        
        logger.info("STT engine initialized")
    
    def _init_nlu(self):
        """Initialize natural language understanding"""
        nlu_config = self.config.get("nlu", {})
        
        self.nlu = IndustrialNLU(
            custom_vocabulary=nlu_config.get("custom_vocabulary")
        )
        
        logger.info("NLU engine initialized")
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        tts_config = self.config.get("tts", {})
        
        self.tts = IndustrialTTS(
            rate=tts_config.get("rate", 150),
            volume=tts_config.get("volume", 1.0),
            voice_id=tts_config.get("voice_id")
        )
        
        logger.info("TTS engine initialized")
    
    def _init_dialogue_manager(self):
        """Initialize dialogue manager"""
        dialogue_config = self.config.get("dialogue", {})
        
        self.dialogue_manager = DialogueManager(
            tts_engine=self.tts,
            confirmation_timeout=dialogue_config.get("timeout_seconds", 30),
            max_retries=dialogue_config.get("max_retries", 3)
        )
        
        logger.info("Dialogue manager initialized")
    
    def _init_integrations(self):
        """Initialize system integrations"""
        integrations = self.config.get("integrations", {})
        
        # ERP connector
        if "erp" in integrations:
            erp_config = integrations["erp"]
            self.erp = ERPConnector(
                base_url=erp_config.get("base_url"),
                api_key=erp_config.get("api_key"),
                timeout=erp_config.get("timeout", 5)
            )
            logger.info("ERP connector initialized")
        else:
            self.erp = None
            logger.warning("ERP connector not configured")
        
        # WMS connector
        if "wms" in integrations:
            wms_config = integrations["wms"]
            self.wms = WMSConnector(
                base_url=wms_config.get("base_url"),
                api_key=wms_config.get("api_key"),
                timeout=wms_config.get("timeout", 5)
            )
            logger.info("WMS connector initialized")
        else:
            self.wms = None
            logger.warning("WMS connector not configured")
    
    def _init_audio_recorder(self):
        """Initialize audio recorder"""
        audio_config = self.config.get("audio", {})
        
        self.recorder = AudioRecorder(
            sample_rate=audio_config.get("sample_rate", 16000),
            channels=audio_config.get("channels", 1),
            device_id=audio_config.get("device_id")
        )
        
        logger.info("Audio recorder initialized")
    
    def _register_handlers(self):
        """Register action handlers for intents"""
        
        # Query inventory
        self.dialogue_manager.register_handler(
            Intent.QUERY_INVENTORY,
            self._handle_query_inventory
        )
        
        # Update inventory
        self.dialogue_manager.register_handler(
            Intent.UPDATE_INVENTORY,
            self._handle_update_inventory
        )
        
        # Query location
        self.dialogue_manager.register_handler(
            Intent.QUERY_LOCATION,
            self._handle_query_location
        )
        
        # Work order next
        self.dialogue_manager.register_handler(
            Intent.WORK_ORDER_NEXT,
            self._handle_work_order_next
        )
        
        # Work order complete
        self.dialogue_manager.register_handler(
            Intent.WORK_ORDER_COMPLETE,
            self._handle_work_order_complete
        )
        
        logger.info("Action handlers registered")
    
    def _handle_query_inventory(self, command) -> dict:
        """Handle inventory query"""
        if not self.wms:
            return {"error": "WMS not configured"}
        
        sku = command.get_entity("sku")
        location = command.get_entity("location")
        
        result = self.wms.get_inventory(
            sku=sku.value,
            location=location.value if location else None
        )
        
        data = result.get("data", {})
        
        return {
            "quantity": data.get("quantity", 0),
            "location": data.get("location", "unknown")
        }
    
    def _handle_update_inventory(self, command) -> dict:
        """Handle inventory update"""
        if not self.wms:
            return {"error": "WMS not configured"}
        
        sku = command.get_entity("sku")
        quantity = command.get_entity("quantity")
        location = command.get_entity("location")
        operation = command.get_entity("operation")
        
        result = self.wms.update_inventory(
            sku=sku.value,
            quantity=int(quantity.value),
            location=location.value if location else "default",
            operation=operation.value if operation else "add"
        )
        
        return result.get("data", {})
    
    def _handle_query_location(self, command) -> dict:
        """Handle location query"""
        if not self.wms:
            return {"error": "WMS not configured"}
        
        sku = command.get_entity("sku")
        pallet = command.get_entity("pallet")
        
        result = self.wms.find_location(
            sku=sku.value if sku else None,
            pallet_id=pallet.value if pallet else None
        )
        
        data = result.get("data", {})
        
        return {
            "location": data.get("location", "unknown")
        }
    
    def _handle_work_order_next(self, command) -> dict:
        """Handle next work order request"""
        if not self.erp:
            return {"error": "ERP not configured"}
        
        worker_id = self.config.get("worker", {}).get("id", "default")
        
        result = self.erp.get_next_work_order(worker_id)
        
        data = result.get("data", {})
        
        return {
            "description": data.get("description", "No pending tasks")
        }
    
    def _handle_work_order_complete(self, command) -> dict:
        """Handle work order completion"""
        if not self.erp:
            return {"error": "ERP not configured"}
        
        # Would need to track current work order
        return {"status": "completed"}
    
    def process_voice_command(self, audio_file: str) -> dict:
        """
        Process voice command from audio file
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Response dictionary
        """
        start_time = datetime.now()
        
        try:
            # Transcribe audio
            transcription = self.stt.transcribe(audio_file)
            text = transcription["text"]
            stt_confidence = transcription["confidence"]
            
            logger.info(f"Transcribed: '{text}' (confidence: {stt_confidence:.2f})")
            
            # Parse command
            parsed_command = self.nlu.parse(text)
            
            # Validate command
            is_valid, error = self.nlu.validate_command(parsed_command)
            
            if not is_valid:
                response = {"status": "error", "message": error}
                self.tts.speak(error)
                return response
            
            # Process through dialogue manager
            response = self.dialogue_manager.process_command(parsed_command)
            
            # Log metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            self.metrics.log_interaction(
                command=text,
                intent=parsed_command.intent.value,
                success=(response.get("status") == "success"),
                latency=elapsed,
                stt_confidence=stt_confidence
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            error_msg = "Sorry, I encountered an error processing your request"
            self.tts.speak(error_msg)
            return {"status": "error", "message": str(e)}
    
    def run(self):
        """Run voice assistant in continuous listening mode"""
        logger.info("Starting voice assistant")
        
        self.tts.speak("Voice assistant ready")
        
        try:
            while True:
                logger.info("Listening for command...")
                
                # Record audio
                audio_file = self.recorder.record_command()
                
                if audio_file:
                    # Process command
                    response = self.process_voice_command(audio_file)
                    logger.info(f"Response: {response}")
        
        except KeyboardInterrupt:
            logger.info("Shutting down voice assistant")
            self.tts.speak("Voice assistant shutting down")
    
    def shutdown(self):
        """Cleanup and shutdown"""
        if self.erp:
            self.erp.close()
        if self.wms:
            self.wms.close()
        
        self.metrics.save_report()
        
        logger.info("Voice assistant shutdown complete")


if __name__ == "__main__":
    import sys
    
    # Get config path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    
    # Create assistant
    assistant = VoiceIndustrialAssistant(config_path)
    
    try:
        # Run assistant
        assistant.run()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    finally:
        assistant.shutdown()
