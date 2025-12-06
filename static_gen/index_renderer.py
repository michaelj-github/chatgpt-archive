"""
Render the main index.html listing all chats.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ingest.db import fetch_all
from ingest.logger import logger


# -----------------------------------------------------------------------------
# Jinja2 environment
# -----------------------------------------------------------------------------

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def get_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Core function
# -----------------------------------------------------------------------------

def render_index_page(output_root: Path) -> Path:
    """
    Generate static_site/index.html by listing all chats in the database.
    """

    # 1) Fetch all chats from DB
    rows = fetch_all(
        """
        SELECT id, chat_id, title, create_time
        FROM chats
        ORDER BY create_time NULLS LAST, id
        """
    )

    chats: List[Dict[str, Any]] = []
    for r in rows:
        chats.append(
            {
                "id": r["id"],
                "chat_id": r["chat_id"],
                "title": r["title"],
                "create_time": r["create_time"],
            }
        )

    # 2) Render index using Jinja
    env = get_env()
    template = env.get_template("index.html")

    html = template.render(
        title="Chat Archive",
        chats=chats,
        css_prefix="",  # index is at static_site/index.html, same folder as assets/
    )

    # 3) Write to static_site/index.html
    ensure_dir(output_root)
    out_path = output_root / "index.html"
    out_path.write_text(html, encoding="utf-8")

    logger.info(f"Rendered index → {out_path}")

    return out_path
