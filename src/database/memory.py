import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "devflow_memory.db",
)


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a database connection and ensure tables exist."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS published_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                title TEXT,
                url TEXT UNIQUE,
                content TEXT,
                channel_id TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS discovered_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                url TEXT UNIQUE,
                deadline TEXT,
                eligibility TEXT,
                status TEXT
            )
            """
        )
    return conn


def is_url_published(url: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a URL was previously published."""
    if not url:
        return False
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM published_posts WHERE url = ? LIMIT 1", (url,))
        return cursor.fetchone() is not None


def get_recently_published(
    days: int = 30,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return posts published within the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, published_at, category, title, url, content, channel_id
            FROM published_posts
            WHERE published_at >= ?
            ORDER BY published_at DESC
            """,
            (cutoff,),
        )
        return [dict(row) for row in cursor.fetchall()]


def record_published(
    title: str,
    url: str,
    category: str = "opportunity",
    content: str = "",
    channel_id: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Record a published post to long-term memory."""
    try:
        with get_db_connection(db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO published_posts (category, title, url, content, channel_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category, title, url, content, str(channel_id)),
            )
        return True
    except sqlite3.Error:
        return False


def record_opportunity(
    name: str,
    url: str,
    deadline: str = "",
    eligibility: str = "",
    status: str = "open",
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Record an opportunity to the database."""
    try:
        with get_db_connection(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO discovered_opportunities (name, url, deadline, eligibility, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, url, deadline, eligibility, status),
            )
        return True
    except sqlite3.Error:
        return False
