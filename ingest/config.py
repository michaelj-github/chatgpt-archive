"""
Configuration module for the ChatGPT Archive ingestion system.

Loads environment variables, defines project-wide settings, and exposes
paths used throughout the ingestion pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load .env file
# -------------------------------------------------------------------
# This loads the environment variables from .env into os.environ.
# If .env is missing, load_dotenv() simply does nothing.
load_dotenv()

# -------------------------------------------------------------------
# Resolve project root
# -------------------------------------------------------------------
# config.py lives in ingest/, so project root is one directory up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Directory paths
# -------------------------------------------------------------------
EXPORT_DIR = PROJECT_ROOT / "exports"          # where raw ChatGPT ZIPs go
STATIC_SITE_DIR = PROJECT_ROOT / "static_site" # generated HTML
BACKUP_DIR = PROJECT_ROOT / "backups"          # backup folders

# Create directories if missing (safe; does nothing if exists)
EXPORT_DIR.mkdir(exist_ok=True)
STATIC_SITE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# Environment Variables
# -------------------------------------------------------------------
DATABASE_URL = os.environ.get("CHAT_ARCHIVE_DB_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "CHAT_ARCHIVE_DB_URL is not set. "
        "Create a .env file in the project root with this entry:\n"
        "CHAT_ARCHIVE_DB_URL=postgresql://postgres:password@localhost/chat_archive"
    )

# -------------------------------------------------------------------
# Config object (recommended)
# -------------------------------------------------------------------
class Config:
    """
    Central configuration object for the entire ingestion system.
    """

    # Database
    DATABASE_URL: str = DATABASE_URL

    # Directories
    PROJECT_ROOT: Path = PROJECT_ROOT
    EXPORT_DIR: Path = EXPORT_DIR
    STATIC_SITE_DIR: Path = STATIC_SITE_DIR
    BACKUP_DIR: Path = BACKUP_DIR

    # Future options (placeholders)
    DEBUG: bool = False
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()


# Export a single global config instance
config = Config()
