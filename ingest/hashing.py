"""
Hashing utilities for the ChatGPT Archive ingestion system.

Provides deterministic SHA-256 hashes for:
    - Individual messages
    - Entire chats (title + ordered messages)

These hashes are used to:
    - Detect new vs. existing chats
    - Detect when a chat has changed since last ingestion
    - Make ingestion idempotent
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional

from ingest.logger import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------

def _canonical_json(obj: Any) -> str:
    """
    Convert a Python object into a canonical JSON string.

    - sort_keys=True ensures deterministic key ordering
    - separators=(',', ':') removes whitespace differences
    - ensure_ascii=False preserves Unicode characters

    This is important so that logically equivalent structures always
    hash to the same value.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_from_string(text: str) -> str:
    """
    Compute SHA-256 hash of a string and return hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_from_bytes(data: bytes) -> str:
    """
    Compute SHA-256 hash of bytes and return hex digest.
    """
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------
# Message hashing
# --------------------------------------------------------------------

VOLATILE_MESSAGE_KEYS = {
    "id",
    "create_time",
    "update_time",
    "timestamp",
    "rating",
    "metadata",  # often non-essential / auto-generated
}


def strip_volatile_fields(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a shallow copy of the message dict with obviously volatile
    fields removed.

    This makes hashes more stable across exports where internal IDs
    or timestamps might change, but the logical content is the same.
    """
    if not isinstance(message, dict):
        # If it's not a dict, just return it as-is.
        return message

    cleaned = dict(message)
    for key in VOLATILE_MESSAGE_KEYS:
        cleaned.pop(key, None)
    return cleaned


def hash_message(raw_message: Dict[str, Any]) -> str:
    """
    Compute a deterministic hash for a single message.

    Strategy:
        - Remove volatile fields
        - Canonicalize JSON
        - SHA-256 of canonical representation
    """
    cleaned = strip_volatile_fields(raw_message)
    canonical = _canonical_json(cleaned)
    digest = _sha256_from_string(canonical)
    logger.debug(f"Hashed message -> {digest}")
    return digest


# --------------------------------------------------------------------
# Chat hashing
# --------------------------------------------------------------------

def hash_chat(
    title: str,
    messages: Iterable[Dict[str, Any]],
    extra_fields: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Compute a deterministic hash for an entire chat.

    Parameters:
        title: Chat title (string)
        messages: Iterable of message JSON objects, in order
        extra_fields: Optional dict of additional metadata to include
                      in the hash (e.g. model name)

    Strategy:
        - Strip volatile fields from each message
        - Preserve message order
        - Build a canonical structure:
              {
                  "title": ...,
                  "messages": [...],
                  "extra": {...}  # optional
              }
        - Hash canonical JSON with SHA-256
    """
    cleaned_messages: List[Dict[str, Any]] = [
        strip_volatile_fields(m) for m in messages
    ]

    payload: Dict[str, Any] = {
        "title": title,
        "messages": cleaned_messages,
    }

    if extra_fields:
        # Only include deterministic extras
        payload["extra"] = extra_fields

    canonical = _canonical_json(payload)
    digest = _sha256_from_string(canonical)
    logger.debug(
        "Hashed chat with %d messages -> %s",
        len(cleaned_messages),
        digest,
    )
    return digest


# --------------------------------------------------------------------
# Convenience helpers for future use
# --------------------------------------------------------------------

def hash_raw_chat_export(raw_chat: Dict[str, Any]) -> str:
    """
    Optional helper: hash a raw chat object from the export JSON.

    This function assumes a structure like:
        {
            "title": "...",
            "mapping": { ... messages ... },
            "model": "...",
            ...
        }

    Since OpenAI may change the export format over time, this helper
    should be adapted to your actual JSON structure. For now, it's
    a generic placeholder.

    You can customize this once you inspect your conversations.json.
    """
    title = raw_chat.get("title", "<untitled>")

    # 'messages' should be a list of message-like objects in order.
    # Depending on the export format, you may need to normalize here.
    messages = raw_chat.get("messages", [])

    extra = {
        "model": raw_chat.get("model"),
        "project_id": raw_chat.get("project_id"),
    }

    return hash_chat(title=title, messages=messages, extra_fields=extra)
