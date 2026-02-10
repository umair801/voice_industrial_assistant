"""
Logging Configuration
Centralized logging setup
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    log_format: str = None
):
    """
    Setup application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for stdout only)
        log_format: Custom log format
    """
    # Default format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Convert level string to constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized (level: {log_level})")


if __name__ == "__main__":
    # Test logging
    setup_logging(log_level="DEBUG", log_file="logs/test.log")
    
    logger = logging.getLogger(__name__)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
