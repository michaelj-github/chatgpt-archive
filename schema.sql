-- ============================================================
-- ChatGPT Archive System - Database Schema
-- ============================================================
-- Stores:
--   • One row per ChatGPT conversation       (chats)
--   • One row per message inside a chat      (messages)
--
-- Designed to:
--   • Preserve all chats indefinitely
--   • Detect changes using hash
--   • Support incremental ingestion
--   • Enable fast browsing and searching
--   • Be future-proof by storing raw JSON
-- ============================================================


-- ============================================================
-- Drop existing tables (optional for development)
-- ============================================================
-- DROP TABLE IF EXISTS messages;
-- DROP TABLE IF EXISTS chats;


-- ============================================================
-- chats table
--   One row per ChatGPT conversation
-- ============================================================

CREATE TABLE IF NOT EXISTS chats (
    id              BIGSERIAL PRIMARY KEY,          -- internal DB id
    chat_id         TEXT UNIQUE NOT NULL,           -- ChatGPT export ID

    -- Basic metadata
    title           TEXT NOT NULL,
    created_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional metadata from export
    model           TEXT,
    project_id      TEXT,
    project_name    TEXT,
    source_file     TEXT,                           -- name of JSON source file

    -- Content & change detection
    hash            TEXT NOT NULL,                  -- SHA256 checksum
    content_text    TEXT NOT NULL,                  -- flattened conversation text
    summary         TEXT,                           -- optional short summary

    -- Full raw JSON document (future-proofing)
    raw_json        JSONB NOT NULL
);


-- ============================================================
-- Indexes for chats
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_chats_chat_id
    ON chats (chat_id);

CREATE INDEX IF NOT EXISTS idx_chats_created_at
    ON chats (created_at);

CREATE INDEX IF NOT EXISTS idx_chats_updated_at
    ON chats (updated_at);

CREATE INDEX IF NOT EXISTS idx_chats_ingested_at
    ON chats (ingested_at);

-- Optional JSONB index for advanced querying:
-- CREATE INDEX IF NOT EXISTS idx_chats_raw_json
--     ON chats USING GIN (raw_json);


-- ============================================================
-- messages table
--   One row per message within a conversation
-- ============================================================

CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL PRIMARY KEY,
    chat_id         BIGINT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,

    message_index   INTEGER NOT NULL,         -- preserves original order
    role            TEXT NOT NULL,            -- 'user', 'assistant', 'system', 'tool'
    created_at      TIMESTAMPTZ,              -- timestamp of the message, if present
    content         TEXT NOT NULL,            -- flattened message text
    raw_json        JSONB NOT NULL            -- full message JSON
);


-- ============================================================
-- Indexes & constraints for messages
-- ============================================================

-- Unique combination ensures idempotency
ALTER TABLE messages
    ADD CONSTRAINT IF NOT EXISTS uq_messages_chat_idx
    UNIQUE (chat_id, message_index);

-- Fast retrieval: "SELECT … WHERE chat_id=X ORDER BY message_index"
CREATE INDEX IF NOT EXISTS idx_messages_chat_id_index
    ON messages (chat_id, message_index);


-- ============================================================
-- Optional Extensions (commented for now)
-- ============================================================

-- -- 1. Full-text search (tsvector)
-- ALTER TABLE chats ADD COLUMN search_vector tsvector;
-- UPDATE chats SET search_vector = to_tsvector('english', content_text);
-- CREATE INDEX idx_chats_search ON chats USING GIN (search_vector);

-- -- 2. Semantic search with pgvector
-- CREATE EXTENSION IF NOT EXISTS vector;
-- ALTER TABLE chats ADD COLUMN embedding vector(1536);

-- -- 3. Tags (key-value classification)
-- CREATE TABLE chat_tags (
--     chat_id BIGINT REFERENCES chats(id) ON DELETE CASCADE,
--     tag TEXT NOT NULL
-- );
-- CREATE INDEX idx_chat_tags_tag ON chat_tags(tag);


-- ============================================================
-- End of Schema
-- ============================================================
