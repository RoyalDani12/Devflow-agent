"""
Settings keyboard builder — generates the inline keyboard for /settings panel.
Kept separate from settings_manager.py to honour the < 250 line rule.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.telegram.settings_manager import (
    get_ai_news_enabled,
    get_auto_publish,
    get_opportunities_enabled,
    get_scan_interval,
)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Build the full settings control-panel inline keyboard."""
    ap_label = "🟢 Auto-Publish: ON" if get_auto_publish() else "🔴 Auto-Publish: OFF"
    interval = get_scan_interval()
    news_label = "✅ AI News" if get_ai_news_enabled() else "⬜ AI News"
    opp_label = "✅ Opportunities" if get_opportunities_enabled() else "⬜ Opportunities"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ap_label, callback_data="settings:auto_publish")],
        [InlineKeyboardButton(f"⏰ Scan: every {interval}h  →  tap to cycle", callback_data="settings:interval")],
        [
            InlineKeyboardButton(news_label, callback_data="settings:ai_news"),
            InlineKeyboardButton(opp_label, callback_data="settings:opportunities"),
        ],
        [InlineKeyboardButton("📊 Memory Stats", callback_data="settings:stats")],
        [InlineKeyboardButton("🔄 Scan Now", callback_data="settings:scan_now")],
    ])
