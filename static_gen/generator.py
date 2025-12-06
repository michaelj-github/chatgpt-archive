"""
Generate the full static HTML site:
  - static_site/index.html
  - static_site/chat/*.html
  - static_site/assets/style.css
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ingest.db import fetch_all
from ingest.logger import logger

from static_gen.index_renderer import render_index_page
from static_gen.chat_renderer import render_chat_page


# -----------------------------------------------------------------------------
# Helper: prepare output directory
# -----------------------------------------------------------------------------

def prepare_output_dir(root: Path, clean: bool = True) -> None:
    """
    Ensure static_site directory exists and optionally wipe it clean.
    """
    if clean and root.exists():
        logger.info(f"Cleaning existing directory: {root}")
        shutil.rmtree(root)

    logger.info(f"Creating directory: {root}")
    root.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Helper: copy CSS assets
# -----------------------------------------------------------------------------

def copy_assets(output_root: Path) -> None:
    """
    Copy assets (currently only style.css) into static_site/assets/
    """
    assets_src = Path(__file__).resolve().parent / "assets"
    assets_dest = output_root / "assets"

    logger.info(f"Copying assets from {assets_src} → {assets_dest}")
    shutil.copytree(assets_src, assets_dest, dirs_exist_ok=True)


# -----------------------------------------------------------------------------
# Main generate function
# -----------------------------------------------------------------------------

def generate_static_site(output_root: Path = Path("static_site")) -> None:
    """
    Generate the entire static HTML archive.
    """
    logger.info("Starting static site generation...")

    # 1) Prepare output directory
    prepare_output_dir(output_root, clean=True)

    # 2) Copy assets
    copy_assets(output_root)

    # 3) Fetch all chats
    chats = fetch_all(
        """
        SELECT id, chat_id, title
        FROM chats
        ORDER BY create_time NULLS LAST, id
        """
    )
    logger.info(f"Found {len(chats)} chats to render.")

    # 4) Render individual chat pages
    for chat in chats:
        chat_id = chat["id"]
        render_chat_page(output_root, chat_id)

    # 5) Render index page
    render_index_page(output_root)

    logger.info("Static site generation complete.")


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    generate_static_site()
