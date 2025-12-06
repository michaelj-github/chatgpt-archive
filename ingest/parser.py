"""
Parser for ChatGPT export JSON structure.

This module:
    - Loads conversations.json
    - Normalizes each chat into a stable internal format
    - Extracts clean text content from message JSON (handles multiple formats)
    - Preserves full raw JSON for archival fidelity
    - Sorts messages correctly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ingest.logger import logger


# ============================================================================
# Utilities
# ============================================================================

def load_conversations_json(path: Path) -> List[Dict[str, Any]]:
    """
    Load ChatGPT's conversations.json export file.
    Returns:
        List of raw chat objects from the export.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Depending on the export version, conversations may be inside "conversations" key.
    if isinstance(data, dict) and "conversations" in data:
        return data["conversations"]

    # Older export: root is a list
    if isinstance(data, list):
        return data

    logger.warning(f"Unexpected conversations.json structure in {path}")
    return []


# ============================================================================
# Message Parsing
# ============================================================================

def extract_message_role(raw_msg: Dict[str, Any]) -> str:
    """
    Determine message role (user/assistant/system).
    Roles vary depending on export format.
    """

    # Newer format: raw_json["author"]["role"]
    author = raw_msg.get("author")
    if isinstance(author, dict):
        role = author.get("role")
        if isinstance(role, str):
            return role

    # Older formats
    return raw_msg.get("role") or "assistant"


def extract_message_content(raw_msg: Dict[str, Any]) -> str:
    """
    Extract the text content from a ChatGPT message in all known export formats.

    Known formats:
        - raw_msg["content"]["parts"] = ["hello", ...]
        - raw_msg["content"] = "text"
        - raw_msg["content"]["text"] = "text"
        - raw_msg["content"] = None or {}
    """

    c = raw_msg.get("content")

    # Format: {"content_type": "text", "parts": ["hello", ...]}
    if isinstance(c, dict):
        parts = c.get("parts")
        if isinstance(parts, list):
            return "\n".join([p for p in parts if isinstance(p, str)]).strip()

        # Format: {"text": "content"}
        if "text" in c and isinstance(c["text"], str):
            return c["text"].strip()

    # Older format: content is a plain string
    if isinstance(c, str):
        return c.strip()

    return ""


# ============================================================================
# Chat Parsing
# ============================================================================

def extract_messages_from_chat(raw_chat: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract a list of normalized messages from a chat.

    Newer OpenAI export formats use:
        chat["mapping"] = {
            "uuid1": {"id": ..., "message": {...}, ...},
            "uuid2": ...
        }

    Older exports had different structures.
    We support both gracefully.
    """

    messages: List[Dict[str, Any]] = []

    # Chat has a "mapping" dict (2023–2024+ format)
    mapping = raw_chat.get("mapping")
    if isinstance(mapping, dict):
        for node in mapping.values():
            msg = node.get("message")
            if not msg:
                continue

            role = extract_message_role(msg)
            content = extract_message_content(msg)

            messages.append({
                "role": role,
                "content": content,
                "raw_json": msg     # Preserve full original message JSON
            })

        # Sort messages by create_time if present, otherwise leave order natural
        def msg_sort_key(m):
            ts = m["raw_json"].get("create_time")
            return ts if isinstance(ts, (int, float)) else 0

        messages.sort(key=msg_sort_key)
        return messages

    # Older exports (rare now)
    # Expect "messages" list directly
    raw_messages = raw_chat.get("messages")
    if isinstance(raw_messages, list):
        for msg in raw_messages:
            role = extract_message_role(msg)
            content = extract_message_content(msg)

            messages.append({
                "role": role,
                "content": content,
                "raw_json": msg
            })

        return messages

    logger.warning(f"Chat {raw_chat.get('id')} has no recognizable message structure.")
    return []


# ============================================================================
# Main normalization function
# ============================================================================

def normalize_chat(raw_chat: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a chat from OpenAI's conversations.json.
    Fields returned:

        chat_id:       unique chat identifier from export
        title:         chat title or fallback
        create_time:   UNIX timestamp (float) or None
        update_time:   UNIX timestamp (float) or None
        model:         model name for the chat
        messages:      list of normalized messages
        raw_json:      full original raw chat JSON
    """

    # Extract basic fields that exist in all new export formats
    chat_id = raw_chat.get("id")
    title = raw_chat.get("title") or "Untitled Chat"
    create_time = raw_chat.get("create_time")
    update_time = raw_chat.get("update_time")
    model = raw_chat.get("model")

    # Extract messages (preserves full raw JSON)
    messages = extract_messages_from_chat(raw_chat)

    normalized = {
        "chat_id": chat_id,
        "title": title,
        "create_time": create_time,
        "update_time": update_time,
        "model": model,
        "messages": messages,
        "raw_json": raw_chat   # Full chat JSON preserved
    }

    return normalized
