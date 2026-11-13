import asyncio
import logging
import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from src.agents.devflow_agent import run_agent
from src.database.memory import record_published
from src.telegram.auth import require_admin
from src.telegram.media_sender import publish_content_with_media, send_draft_for_review
from src.workflows.daily_workflow import generate_daily_draft

logger = logging.getLogger("DevFlowBot")
pending_drafts: dict[int, str] = {}


def _publish_chat_id(review_chat_id: int) -> int:
    configured_chat_id = os.getenv("TELEGRAM_PUBLISH_CHAT_ID")
    if not configured_chat_id:
        return review_chat_id
    try:
        return int(configured_chat_id)
    except ValueError as exc:
        raise ValueError("TELEGRAM_PUBLISH_CHAT_ID must be a numeric chat ID") from exc


async def _execute_publish(context: ContextTypes.DEFAULT_TYPE, review_chat_id: int) -> bool:
    draft = pending_drafts.get(review_chat_id)
    if not draft or (isinstance(draft, str) and not draft.strip()):
        pending_drafts.pop(review_chat_id, None)
        return False

    publish_chat_id = _publish_chat_id(review_chat_id)
    await publish_content_with_media(context.bot, publish_chat_id, draft)

    draft_str = " ".join(draft) if isinstance(draft, list) else str(draft)
    for url in re.findall(r"https?://[^\s\)\>]+", draft_str):
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
        "🎯 Tech Opportunities & Fellowships (Auto-deduplicated)\n"
        "💻 Coding & Developer Guidance\n\n"
        "Commands:\n"
        "/draft - Generate fresh, unseen opportunities\n"
        "/approve - Publish pending draft\n"
        "/reject - Discard draft"
    )

    if latest_cached_briefing:
        pending_drafts[chat_id] = latest_cached_briefing
        await send_draft_for_review(
            context.bot,
            chat_id,
            latest_cached_briefing,
            header="📋 **Latest verified briefing ready for review:**",
        )


@require_admin
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **DevFlow Owner Commands**\n\n"
        "/start - Authenticate & register this chat\n"
        "/draft - Run research scan & prepare draft with banner\n"
        "/approve - Publish current pending draft to channel\n"
        "/reject - Discard current pending draft\n"
        "/chatid - View this chat's ID\n\n"
        "Or simply ask me any technical question or request."
    )


@require_admin
async def chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your User ID: `{update.effective_user.id}`\nChat ID: `{update.effective_chat.id}`",
        parse_mode="Markdown",
    )


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
    review_chat_id = update.effective_chat.id
    if review_chat_id not in pending_drafts:
        await update.message.reply_text("There is no pending draft to publish.")
        return
    success = await _execute_publish(context, review_chat_id)
    msg = "✅ Draft published successfully with media." if success else "Draft was empty."
    await update.message.reply_text(msg)


@require_admin
async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if pending_drafts.pop(update.effective_chat.id, None) is None:
        await update.message.reply_text("There is no pending draft to reject.")
        return
    await update.message.reply_text("🗑️ Draft discarded.")


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


@require_admin
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.telegram.bot import split_message

    if not update.message or not update.message.text:
        return
    user_message = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = await asyncio.to_thread(run_agent, user_message) or "No response generated."
        for chunk in split_message(response):
            await update.message.reply_text(chunk)
    except Exception as exc:
        logger.exception("Message handling failed")
        await update.message.reply_text(f"Error: {exc}")
