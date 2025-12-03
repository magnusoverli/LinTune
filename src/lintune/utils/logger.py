"""
Logging configuration for LinTune

Writes logs to both console and file for debugging.
Also captures stderr (Qt warnings) to log file.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


# Log file location
LOG_DIR = Path.home() / ".local" / "share" / "lintune"
LOG_FILE = LOG_DIR / "lintune.log"


class StderrCapture:
    """Captures stderr and writes to both original stderr and log file"""
    
    def __init__(self, log_file: Path, original_stderr):
        self.log_file = log_file
        self.original_stderr = original_stderr
        self.file_handle = open(log_file, 'a', encoding='utf-8')
    
    def write(self, message):
        # Write to original stderr
        self.original_stderr.write(message)
        # Also write to log file (with prefix for Qt messages)
        if message.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.file_handle.write(f"{timestamp} | STDERR   | qt | {message}")
            if not message.endswith('\n'):
                self.file_handle.write('\n')
            self.file_handle.flush()
    
    def flush(self):
        self.original_stderr.flush()
        self.file_handle.flush()
    
    def close(self):
        self.file_handle.close()


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Setup application logging
    
    Args:
        debug: Enable debug level logging
        
    Returns:
        Configured logger
    """
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Capture stderr (Qt warnings go here)
    sys.stderr = StderrCapture(LOG_FILE, sys.__stderr__)
    
    # Create logger
    logger = logging.getLogger("lintune")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Format
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler - always debug level for troubleshooting
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    
    # Log startup
    logger.info("=" * 60)
    logger.info("LinTune started")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)
    
    return logger


def get_logger(name: str = "lintune") -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def get_log_file() -> Path:
    """Get log file path"""
    return LOG_FILE

