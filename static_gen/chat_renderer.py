"""
Render individual chat pages as static HTML.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ingest.db import fetch_one, fetch_all
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


def nl2br(text: str) -> str:
    """
    Simple newline-to-<br> conversion for plain text messages.
    (For MVP we won't do full markdown rendering yet.)
    """
    if not text:
        return ""
    # Escape basic HTML special chars, then replace newlines
    escaped = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
    return escaped.replace("\n", "<br>\n")


# -----------------------------------------------------------------------------
# Core render function
# -----------------------------------------------------------------------------

def render_chat_page(output_root: Path, chat_db_id: int) -> Path:
    """
    Render a single chat (by DB id) to static_site/chat/<chat_id>.html.

    Returns the path to the generated file.
    """
    # 1) Fetch chat row
    chat_row = fetch_one(
        """
        SELECT id, chat_id, title, create_time, update_time, model
        FROM chats
        WHERE id = %s
        """,
        (chat_db_id,),
    )

    if chat_row is None:
        raise ValueError(f"Chat id {chat_db_id} not found in database.")

    # 2) Fetch messages for this chat
    msg_rows = fetch_all(
        """
        SELECT message_index, role, content
        FROM messages
        WHERE chat_id = %s
        ORDER BY message_index
        """,
        (chat_db_id,),
    )

    # 3) Prepare data for template
    messages: List[Dict[str, Any]] = []
    for m in msg_rows:
        messages.append(
            {
                "role": m["role"],
                "content": nl2br(m["content"] or ""),
            }
        )

    chat = {
        "id": chat_row["id"],
        "chat_id": chat_row["chat_id"],
        "title": chat_row["title"],
        "create_time": chat_row["create_time"],
        "update_time": chat_row["update_time"],
        "model": chat_row["model"],
    }

    # 4) Jinja render
    env = get_env()
    template = env.get_template("chat.html")

    html = template.render(
        title=chat["title"],
        chat=chat,
        messages=messages,
        css_prefix="../",  # because chat pages live in /chat/
    )

    # 5) Write to static_site/chat/<chat_id>.html
    chat_dir = output_root / "chat"
    ensure_dir(chat_dir)

    filename = f"{chat['chat_id']}.html"
    out_path = chat_dir / filename

    out_path.write_text(html, encoding="utf-8")
    logger.info(f"Rendered chat {chat['chat_id']} → {out_path}")

    return out_path
