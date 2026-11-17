"""
Core Telegram command handlers for DevFlow Agent.
Settings & message routing live in settings_handlers.py and message_handler.py.
All < 250 lines.
"""
import asyncio
import logging
import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from src.database.memory import record_published
from src.telegram.auth import require_admin
from src.telegram.media_sender import publish_content_with_media, send_draft_for_review
from src.workflows.daily_workflow import generate_daily_draft

logger = logging.getLogger("DevFlowBot")
pending_drafts: dict[int, str] = {}


def _publish_chat_id(review_chat_id: int) -> int | str:
    configured_chat_id = os.getenv("TELEGRAM_PUBLISH_CHAT_ID")
    if not configured_chat_id:
        return review_chat_id
    configured = configured_chat_id.strip()
    if configured.startswith("@"):
        return configured
    try:
        return int(configured)
    except ValueError:
        return configured


async def _execute_publish(context: ContextTypes.DEFAULT_TYPE, review_chat_id: int) -> bool:
    draft = pending_drafts.get(review_chat_id)
    if not draft or (isinstance(draft, str) and not draft.strip()):
        pending_drafts.pop(review_chat_id, None)
        return False

    publish_chat_id = _publish_chat_id(review_chat_id)
    await publish_content_with_media(context.bot, publish_chat_id, draft)

    draft_str = " ".join(draft) if isinstance(draft, list) else str(draft)
    for url in re.findall(r"https?://[^\s\)>]+", draft_str):
        record_published("Daily Broadcast Update", url, "daily_post", draft_str[:400], str(publish_chat_id))

    del pending_drafts[review_chat_id]
    return True


@require_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.services.scheduler import latest_cached_briefing, set_active_admin_chat

    chat_id = update.effective_chat.id
    set_active_admin_chat(chat_id)

    await update.message.reply_text(
        "👋 Welcome back, Owner!\n\n"
        "🔒 Authentication verified. Only you can control this agent.\n\n"
        "🚀 AI News & Tech Trends\n"
        "🎯 Tech Opportunities & Fellowships\n"
        "💻 Coding & Developer Guidance\n\n"
        "Commands:\n"
        "/draft     — Generate fresh reviewable cards\n"
        "/approve   — Publish all pending cards\n"
        "/reject    — Discard all pending cards\n"
        "/settings  — Open control panel"
    )

    if latest_cached_briefing:
        pending_drafts[chat_id] = latest_cached_briefing
        await send_draft_for_review(
            context.bot,
            chat_id,
            latest_cached_briefing,
            header="📋 Latest verified briefing ready for review:",
        )


@require_admin
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 DevFlow Owner Commands\n\n"
        "/start     — Authenticate and register this chat\n"
        "/draft     — Run research scan and prepare review cards\n"
        "/approve   — Publish all pending cards to channel\n"
        "/reject    — Discard all pending cards\n"
        "/settings  — Open the in-chat control panel\n"
        "/chatid    — View this chat ID\n\n"
        "Or type a topic (e.g. 'AI hackathon') to search instantly."
    )


@require_admin
async def chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    response = (
        f"👤 Your User ID: `{update.effective_user.id}`\n"
        f"💬 Current Chat ID: `{update.effective_chat.id}`\n"
    )
    forward_chat = getattr(msg, "forward_from_chat", None)
    if forward_chat:
        response += (
            f"\n📢 Forwarded Channel: *{forward_chat.title}*\n"
            f"🆔 Channel ID: `{forward_chat.id}`\n\n"
            f"👉 Put this in your `.env`:\n`TELEGRAM_PUBLISH_CHAT_ID={forward_chat.id}`"
        )
    else:
        response += (
            "\n💡 *How to link your Channel:*\n"
            "1. Add this bot as an **Administrator** in your channel.\n"
            "2. Forward any post from your channel to this chat.\n"
            "3. I'll automatically give you the Channel ID!"
        )
    await update.message.reply_text(response, parse_mode="Markdown")


@require_admin
async def draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        draft = await asyncio.to_thread(generate_daily_draft)
        if not draft or not draft.strip():
            await update.message.reply_text("No new publishable content found.")
            return

        pending_drafts[chat_id] = draft
        await send_draft_for_review(context.bot, chat_id, draft)
    except Exception as exc:
        logger.exception("Draft generation failed")
        await update.message.reply_text(f"Draft error: {exc}")


@require_admin
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.telegram.card_manager import get_all_pending_cards, pop_card

    review_chat_id = update.effective_chat.id
    pending_cards_list = get_all_pending_cards()
    if not pending_cards_list and review_chat_id not in pending_drafts:
        await update.message.reply_text("There are no pending items to publish.")
        return

    count = 0
    publish_chat_id = _publish_chat_id(review_chat_id)
    for card in pending_cards_list:
        await publish_content_with_media(context.bot, publish_chat_id, card.text)
        for url in re.findall(r"https?://[^\s\)>]+", card.text):
            record_published("Card Broadcast", url, card.category, card.text[:400], str(publish_chat_id))
        pop_card(card.card_id)
        count += 1

    if review_chat_id in pending_drafts:
        await _execute_publish(context, review_chat_id)
        count += 1

    await update.message.reply_text(f"✅ Published {count} item(s) to the channel.")


@require_admin
async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.telegram.card_manager import clear_all_cards, get_all_pending_cards

    had_cards = len(get_all_pending_cards()) > 0
    clear_all_cards()
    had_draft = pending_drafts.pop(update.effective_chat.id, None) is not None
    if not had_cards and not had_draft:
        await update.message.reply_text("There are no pending items to reject.")
        return
    await update.message.reply_text("🗑️ All pending items discarded.")


@require_admin
async def handle_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle granular approve/reject clicks for individual cards."""
    from src.telegram.card_manager import get_card, pop_card

    query = update.callback_query
    await query.answer()
    data = query.data or ""
    parts = data.split(":")
    if len(parts) < 3:
        return
    action, card_id = parts[1], parts[2]
    chat_id = query.message.chat_id

    card = get_card(card_id)
    if not card:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("⚠️ This item is no longer pending or already processed.")
        return

    if action == "approve":
        publish_chat_id = _publish_chat_id(chat_id)
        await publish_content_with_media(context.bot, publish_chat_id, card.text)
        for url in re.findall(r"https?://[^\s\)>]+", card.text):
            record_published("Individual Card Broadcast", url, card.category, card.text[:400], str(publish_chat_id))
        pop_card(card_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Published this card to the channel!")

    elif action == "reject":
        pop_card(card_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🗑️ Discarded this item.")


@require_admin
async def handle_draft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    action = query.data

    if action == "draft:approve":
        success = await _execute_publish(context, chat_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Draft published to channel with media!" if success else "Draft empty.")
    elif action == "draft:reject":
        pending_drafts.pop(chat_id, None)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🗑️ Draft discarded.")
    elif action == "draft:regenerate":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🔄 Researching fresh unseen items...")
        draft = await asyncio.to_thread(generate_daily_draft)
        if draft and draft.strip():
            pending_drafts[chat_id] = draft
            await send_draft_for_review(context.bot, chat_id, draft)
        else:
            await query.message.reply_text("No new content found during refresh.")
