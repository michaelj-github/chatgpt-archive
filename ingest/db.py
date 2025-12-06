"""
Database connection manager for the ChatGPT Archive ingestion system.

Provides:
    - get_connection(): Create a new psycopg2 connection
    - execute(): Run INSERT/UPDATE/DELETE
    - fetch_one(), fetch_all(): Read queries
    - transaction(): Context manager for safe DB transactions

All settings come from ingest.config.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager

from ingest.config import config
from ingest.logger import get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# Connection Factory
# ----------------------------------------------------------------------
def get_connection():
    """
    Create a new PostgreSQL connection using DATABASE_URL.

    Returns:
        psycopg2 connection object
    """
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


# ----------------------------------------------------------------------
# Transaction Context Manager
# ----------------------------------------------------------------------
@contextmanager
def transaction():
    """
    Provides a transaction context:

        with transaction() as cur:
            cur.execute(...)
            cur.execute(...)

    Automatically commits on success or rolls back on failure.
    """

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------------------
# Query Helpers
# ----------------------------------------------------------------------
def execute(query: str, params: tuple = None):
    """Run an INSERT/UPDATE/DELETE query."""
    with transaction() as cur:
        cur.execute(query, params or ())


def fetch_one(query: str, params: tuple = None):
    """Return a single row or None."""
    with transaction() as cur:
        cur.execute(query, params or ())
        return cur.fetchone()


def fetch_all(query: str, params: tuple = None):
    """Return all matching rows."""
    with transaction() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()
