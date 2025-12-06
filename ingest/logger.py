"""
Logging utility for the ChatGPT Archive ingestion system.

Provides a unified logger with consistent formatting, log levels loaded from
environment variables, and optional file logging.
"""

import logging
import sys
from pathlib import Path
from ingest.config import config


def get_logger(name: str = "chatgpt_archive") -> logging.Logger:
    """
    Returns a configured logger instance with standard formatting.

    Usage:
        logger = get_logger(__name__)
        logger.info("Message...")
    """

    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(config.LOG_LEVEL)

    # ------------------------------------------------------------------
    # Console Handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Optional File Logging (disabled by default)
    # ------------------------------------------------------------------
    # Uncomment this block if you'd like to write logs to a file.
    #
    # logs_dir = config.PROJECT_ROOT / "logs"
    # logs_dir.mkdir(exist_ok=True)
    #
    # file_handler = logging.FileHandler(logs_dir / "ingestion.log")
    # file_handler.setFormatter(console_format)
    # logger.addHandler(file_handler)

    return logger


# Default global logger
logger = get_logger()
