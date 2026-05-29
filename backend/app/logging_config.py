#!/usr/bin/env python3
"""
Logging Configuration - Standard Python Logging
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging with standard format"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("FloatChat")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # === Console Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # ✅ Standard format (no Rich tags)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    
    # === File Handler (rotating) ===
    file_handler = RotatingFileHandler(
        log_dir / "floatchat.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Standard format for file
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent log propagation to root logger (avoids duplicate logs)
    logger.propagate = False
    
    return logger


# Global logger instance
logger = setup_logging()