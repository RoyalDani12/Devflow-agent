"""
In-chat settings management for DevFlow Agent.
Stores toggleable settings in SQLite agent_settings table.
All < 250 lines.
"""
import logging
from src.database.memory import get_db_connection

logger = logging.getLogger("DevFlowSettings")

# ─── Default Values ────────────────────────────────────────────────────────────
DEFAULTS: dict[str, str] = {
    "auto_publish": "false",
    "scan_interval": "24",   # hours: 6, 12, 24
    "ai_news_enabled": "true",
    "opportunities_enabled": "true",
}

INTERVAL_CYCLE = ["6", "12", "24"]


def _get(key: str) -> str:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT value FROM agent_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else DEFAULTS.get(key, "")
    finally:
        conn.close()


def _set(key: str, value: str) -> None:
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO agent_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
    finally:
        conn.close()


# ─── Public Accessors ──────────────────────────────────────────────────────────

def get_auto_publish() -> bool:
    return _get("auto_publish") in {"true", "1", "yes"}


def toggle_auto_publish() -> bool:
    new_val = "false" if get_auto_publish() else "true"
    _set("auto_publish", new_val)
    return new_val == "true"


def get_scan_interval() -> str:
    return _get("scan_interval") or "24"


def cycle_scan_interval() -> str:
    current = get_scan_interval()
    idx = INTERVAL_CYCLE.index(current) if current in INTERVAL_CYCLE else 2
    new_val = INTERVAL_CYCLE[(idx + 1) % len(INTERVAL_CYCLE)]
    _set("scan_interval", new_val)
    return new_val


def get_ai_news_enabled() -> bool:
    return _get("ai_news_enabled") != "false"


def toggle_ai_news() -> bool:
    new_val = "false" if get_ai_news_enabled() else "true"
    _set("ai_news_enabled", new_val)
    return new_val == "true"


def get_opportunities_enabled() -> bool:
    return _get("opportunities_enabled") != "false"


def toggle_opportunities() -> bool:
    new_val = "false" if get_opportunities_enabled() else "true"
    _set("opportunities_enabled", new_val)
    return new_val == "true"


# ─── Keyboard Builder ──────────────────────────────────────────────────────────

def build_settings_text() -> str:
    ap = "🟢 ON" if get_auto_publish() else "🔴 OFF"
    interval = get_scan_interval() + "h"
    news_icon = "✅" if get_ai_news_enabled() else "⬜"
    opp_icon = "✅" if get_opportunities_enabled() else "⬜"
    return (
        "⚙️  DEVFLOW AGENT — CONTROL PANEL\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• Auto-Publish to Channel:  {ap}\n"
        f"• Scan Interval:            every {interval}\n"
        f"• AI News Feed:             {news_icon}\n"
        f"• Opportunities Feed:       {opp_icon}\n\n"
        "Tap a button below to toggle or trigger:"
    )
