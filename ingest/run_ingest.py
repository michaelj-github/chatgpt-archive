"""
Main ingestion pipeline for the ChatGPT Archive system.

Steps:
    1. Load conversations.json from a ChatGPT export directory
    2. Normalize each chat
    3. Compute chat hash
    4. Check database for existing chat
    5. Insert new chats OR update changed chats
    6. Insert ordered messages
    7. Print summary

This module orchestrates the entire ingestion workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from ingest.logger import logger
from ingest.config import config
from ingest.db import fetch_one, fetch_all, execute
from ingest.parser import load_conversations_json, normalize_chat
from ingest.hashing import hash_chat


# ============================================================================
# Helper: Flatten content_text for full-text search and browsing
# ============================================================================

def flatten_content(messages: List[Dict[str, Any]]) -> str:
    """
    Combine all text messages into a single searchable/browsable string.
    """
    parts = []
    for msg in messages:
        text = msg.get("content") or ""
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())

    return "\n".join(parts).strip()


# ============================================================================
# Locate conversations.json inside an export folder
# ============================================================================

def find_conversations_json(export_dir: Path) -> Path:
    """
    Locate conversations.json inside the given export directory.
    """
    candidates = list(export_dir.glob("**/conversations.json"))

    if not candidates:
        raise FileNotFoundError(f"No conversations.json found in {export_dir}")

    if len(candidates) > 1:
        logger.warning(
            "Multiple conversations.json files found. Using the first: %s",
            candidates[0],
        )

    return candidates[0]


# ============================================================================
# Database Insert/Update Helpers
# ============================================================================

def upsert_chat(normalized: Dict[str, Any], chat_hash: str) -> int:
    """
    Insert a new chat or update an existing one.
    Returns:
        chat_id (database id)
    """

    # Try to find existing chat by chat_id from export
    existing = fetch_one(
        "SELECT id, hash FROM chats WHERE chat_id = %s",
        (normalized["chat_id"],),
    )

    # Prepare flattened content and raw JSON to store
    content_text = flatten_content(normalized["messages"])
    raw_json_text = json.dumps(normalized, ensure_ascii=False)

    # ----------------------------------------------------------------------
    # INSERT NEW CHAT
    # ----------------------------------------------------------------------
    if existing is None:
        logger.info(f"Inserting new chat: {normalized['title'][:60]}")

        result = fetch_one(
            """
            INSERT INTO chats (
                chat_id, title,
                create_time, update_time,
                model, hash,
                content_text, raw_json
            )
            VALUES (
                %s, %s,
                to_timestamp(%s), to_timestamp(%s),
                %s, %s,
                %s, %s
            )
            RETURNING id
            """,
            (
                normalized["chat_id"],
                normalized["title"],
                normalized["create_time"] or 0,
                normalized["update_time"] or 0,
                normalized["model"],
                chat_hash,
                content_text,
                raw_json_text,
            ),
        )

        return result["id"]

    # ----------------------------------------------------------------------
    # UPDATE EXISTING CHAT (if hash changed)
    # ----------------------------------------------------------------------
    existing_hash = existing["hash"]

    if existing_hash == chat_hash:
        logger.info(f"No changes: {normalized['title'][:60]}")
        return existing["id"]

    logger.info(f"Updating modified chat: {normalized['title'][:60]}")

    chat_db_id = existing["id"]

    # Update chat row
    execute(
        """
        UPDATE chats
        SET title = %s,
            create_time = to_timestamp(%s),
            update_time = to_timestamp(%s),
            model = %s,
            hash = %s,
            content_text = %s,
            raw_json = %s
        WHERE id = %s
        """,
        (
            normalized["title"],
            normalized["create_time"] or 0,
            normalized["update_time"] or 0,
            normalized["model"],
            chat_hash,
            content_text,
            raw_json_text,
            chat_db_id,
        ),
    )

    # Remove old messages (they will be reinserted)
    execute("DELETE FROM messages WHERE chat_id = %s", (chat_db_id,))

    return chat_db_id


def insert_messages(chat_db_id: int, messages: List[Dict[str, Any]]):
    """
    Insert a list of messages for a chat_id, preserving message_index.
    """
    for index, msg in enumerate(messages):
        execute(
            """
            INSERT INTO messages (
                chat_id, message_index,
                role, created_at, content, raw_json
            )
            VALUES (%s, %s, %s, NULL, %s, %s)
            """,
            (
                chat_db_id,
                index,
                msg["role"],
                msg["content"],
                json.dumps(msg["raw_json"], ensure_ascii=False),
            ),
        )


# ============================================================================
# Main Ingestion Pipeline
# ============================================================================

def ingest_export(export_path: Path):
    """
    Given a path to a ChatGPT export directory,
    run the full ingestion pipeline.
    """

    logger.info(f"Starting ingestion from: {export_path}")

    conversations_path = find_conversations_json(export_path)
    raw_chats = load_conversations_json(conversations_path)

    logger.info(f"Loaded {len(raw_chats)} chats from export.")

    new_count = 0
    updated_count = 0
    unchanged_count = 0

    for raw_chat in raw_chats:
        normalized = normalize_chat(raw_chat)
        messages = normalized["messages"]

        # Hash for change detection
        chat_hash = hash_chat(
            title=normalized["title"],
            messages=messages,
            extra_fields={"model": normalized["model"]},
        )

        old_row = fetch_one(
            "SELECT id, hash FROM chats WHERE chat_id = %s",
            (normalized["chat_id"],)
        )

        chat_db_id = upsert_chat(normalized, chat_hash)

        if old_row is None:
            new_count += 1
        elif old_row["hash"] != chat_hash:
            updated_count += 1
        else:
            unchanged_count += 1
            continue

        # Insert messages (unless chat was unchanged)
        insert_messages(chat_db_id, messages)

    logger.info("Ingestion complete.")
    logger.info(f"New chats: {new_count}")
    logger.info(f"Updated chats: {updated_count}")
    logger.info(f"Unchanged chats: {unchanged_count}")


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest a ChatGPT export folder.")
    parser.add_argument(
        "export_dir",
        type=str,
        help="Path to the directory containing conversations.json."
    )

    args = parser.parse_args()
    ingest_export(Path(args.export_dir).resolve())
