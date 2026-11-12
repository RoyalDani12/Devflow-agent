from datetime import datetime, timedelta, timezone
import os
import sqlite3
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
                status TEXT,
                seen_count INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        try:
            conn.execute("ALTER TABLE discovered_opportunities ADD COLUMN seen_count INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
    return conn


def get_stored_admin_id(db_path: str = DEFAULT_DB_PATH) -> int | None:
    """Retrieve the owner user ID from database."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM agent_settings WHERE key = 'admin_user_id'")
        row = cursor.fetchone()
        return int(row["value"]) if row else None
    finally:
        conn.close()


def set_stored_admin_id(user_id: int, db_path: str = DEFAULT_DB_PATH) -> None:
    """Persist the owner user ID so only the owner can access the bot."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO agent_settings (key, value) VALUES ('admin_user_id', ?)",
                (str(user_id),),
            )
    finally:
        conn.close()


def is_url_published(url: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a URL was previously published to the channel."""
    if not url:
        return False
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM published_posts WHERE url = ? LIMIT 1", (url,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_recently_published(
    days: int = 30,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return posts published within the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = get_db_connection(db_path)
    try:
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
    finally:
        conn.close()


def record_published(
    title: str,
    url: str,
    category: str = "opportunity",
    content: str = "",
    channel_id: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Record a published post to long-term memory."""
    conn = get_db_connection(db_path)
    try:
        with conn:
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
    finally:
        conn.close()


def record_opportunity(
    name: str,
    url: str,
    deadline: str = "",
    eligibility: str = "",
    status: str = "open",
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Record or update an opportunity and increment seen count."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO discovered_opportunities (name, url, deadline, eligibility, status, seen_count)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(url) DO UPDATE SET seen_count = seen_count + 1, status = excluded.status
                """,
                (name, url, deadline, eligibility, status),
            )
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_seen_opportunity_urls(db_path: str = DEFAULT_DB_PATH) -> set[str]:
    """Return all URLs that have already been recommended or published."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM published_posts UNION SELECT url FROM discovered_opportunities WHERE seen_count > 1")
        return {row["url"] for row in cursor.fetchall() if row["url"]}
    finally:
        conn.close()
