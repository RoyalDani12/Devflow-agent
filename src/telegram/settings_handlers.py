"""
Settings & free-text message handlers for DevFlow Agent.
Split from handlers.py to keep all files < 250 lines.
"""
import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.agents.devflow_agent import run_agent
from src.telegram.auth import require_admin
from src.telegram.media_sender import send_draft_for_review
from src.telegram.handlers import generate_daily_draft, pending_drafts

logger = logging.getLogger("DevFlowBot")

_SEARCH_KEYWORDS = {
    "hackathon", "fellowship", "scholarship", "grant", "internship",
    "bootcamp", "competition", "contest", "bounty", "job", "remote",
    "ai", "ml", "llm", "python", "rust", "web3", "blockchain",
    "frontend", "backend", "fullstack", "devops", "cloud",
    "ethiopia", "africa", "europe", "usa", "canada", "germany",
    "2025", "2026", "2027", "funding", "startup", "open source",
}


def _is_search_query(text: str) -> bool:
    lower = text.lower()
    if any(kw in lower for kw in _SEARCH_KEYWORDS):
        return True
    return len(text.split()) <= 3 and len(text) >= 3


@require_admin
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the in-chat settings control panel."""
    from src.telegram.settings_manager import build_settings_text
    from src.telegram.settings_buttons import get_settings_keyboard

    text = build_settings_text()
    keyboard = get_settings_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)


@require_admin
async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all settings:* button presses."""
    from src.telegram.settings_manager import (
        build_settings_text,
        cycle_scan_interval,
        toggle_ai_news,
        toggle_auto_publish,
        toggle_opportunities,
    )
    from src.telegram.settings_buttons import get_settings_keyboard
    from src.database.memory import get_recently_published

    query = update.callback_query
    await query.answer()
    action = (query.data or "").replace("settings:", "")

    if action == "auto_publish":
        new_state = toggle_auto_publish()
        label = "🟢 Auto-Publish is now ON — items go live immediately."
        if not new_state:
            label = "🔴 Auto-Publish is now OFF — you review each card first."
        await query.answer(label, show_alert=True)

    elif action == "interval":
        new_h = cycle_scan_interval()
        await query.answer(f"⏰ Scan interval set to every {new_h}h", show_alert=True)

    elif action == "ai_news":
        state = toggle_ai_news()
        await query.answer("✅ AI News feed enabled." if state else "⬜ AI News feed disabled.", show_alert=True)

    elif action == "opportunities":
        state = toggle_opportunities()
        await query.answer(
            "✅ Opportunities feed enabled." if state else "⬜ Opportunities feed disabled.",
            show_alert=True,
        )

    elif action == "scan_now":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🔄 Launching instant research scan...")
        draft = await asyncio.to_thread(generate_daily_draft)
        chat_id = query.message.chat_id
        if draft and draft.strip():
            pending_drafts[chat_id] = draft
            await send_draft_for_review(context.bot, chat_id, draft)
        else:
            await query.message.reply_text("No new content found right now. Try again later.")
        return

    elif action == "stats":
        recent = get_recently_published(days=30)
        msg = (
            "📊  MEMORY STATS (last 30 days)\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Published posts:  {len(recent)}\n"
        )
        await query.answer(msg, show_alert=True)
        return

    # Refresh panel after any toggle
    try:
        await query.edit_message_text(build_settings_text(), reply_markup=get_settings_keyboard())
    except Exception:
        pass


@require_admin
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route free text: search query → targeted research; casual → guidance."""
    from src.telegram.bot import split_message

    if not update.message or not update.message.text:
        return
    user_message = update.message.text.strip()
    if len(user_message) < 2:
        return

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        if _is_search_query(user_message):
            await update.message.reply_text(f"🔍 Searching: {user_message}\n\nScanning sources...")
            prompt = (
                f"Find the best current opportunities, hackathons, fellowships, "
                f"AI news, or resources related to: {user_message}. "
                f"Return 3-5 real, specific, actionable items with URLs. "
                f"No markdown asterisks. Plain text only."
            )
            response = await asyncio.to_thread(run_agent, prompt) or "No results found."
            for chunk in split_message(response):
                await update.message.reply_text(chunk)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Generate Cards", callback_data="draft:regenerate")],
                [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings:open")],
            ])
            await update.message.reply_text(
                "👋 Use /draft to generate new cards or /settings to control the agent.",
                reply_markup=keyboard,
            )

    except Exception as exc:
        logger.exception("Message handling failed")
        await update.message.reply_text(f"Search error: {exc}")
