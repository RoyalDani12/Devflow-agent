import asyncio
import logging
import os
import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.agents.devflow_agent import run_agent
from src.database.memory import record_published
from src.workflows.daily_workflow import generate_daily_draft

logger = logging.getLogger(__name__)
MAX_TELEGRAM_MESSAGE_LENGTH = 4000
pending_drafts: dict[int, str] = {}


def split_message(message: str) -> list[str]:
    """Split a response into chunks that Telegram can accept."""
    chunks = []
    remaining = message

    while len(remaining) > MAX_TELEGRAM_MESSAGE_LENGTH:
        split_at = remaining.rfind(
            "\n",
            0,
            MAX_TELEGRAM_MESSAGE_LENGTH,
        )
        if split_at <= 0:
            split_at = remaining.rfind(
                " ",
                0,
                MAX_TELEGRAM_MESSAGE_LENGTH,
            )
        if split_at <= 0:
            split_at = MAX_TELEGRAM_MESSAGE_LENGTH

        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()

    remaining = remaining.strip()
    if remaining:
        chunks.append(remaining)

    return chunks


def get_draft_review_keyboard() -> InlineKeyboardMarkup:
    """Return interactive inline buttons for draft approval."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve & Publish", callback_data="draft:approve"),
            InlineKeyboardButton("🔄 Regenerate", callback_data="draft:regenerate"),
        ],
        [
            InlineKeyboardButton("❌ Discard", callback_data="draft:reject"),
        ],
    ])


def _publish_chat_id(review_chat_id: int) -> int:
    configured_chat_id = os.getenv("TELEGRAM_PUBLISH_CHAT_ID")
    if not configured_chat_id:
        return review_chat_id
    try:
        return int(configured_chat_id)
    except ValueError as exc:
        raise ValueError("TELEGRAM_PUBLISH_CHAT_ID must be a numeric chat ID") from exc


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id
    from src.services.scheduler import latest_cached_briefing, set_active_admin_chat
    set_active_admin_chat(chat_id)

    await update.message.reply_text(
        "Hey! 👋 Welcome to DevFlow AI!\n\n"
        "I'm your autonomous developer assistant.\n\n"
        "🚀 AI News & Tech Trends\n"
        "🎯 Tech Opportunities & Fellowships\n"
        "💻 Coding & Developer Guidance\n\n"
        "I have registered this chat to receive daily autonomous briefings.\n"
        "Send me any question, or use /draft to trigger a fresh research scan."
    )

    if latest_cached_briefing:
        chunks = split_message(latest_cached_briefing)
        pending_drafts[chat_id] = "\n\n".join(chunks)
        await update.message.reply_text("📋 **Here is the latest briefing I verified:**", parse_mode="Markdown")
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await update.message.reply_text(
                    chunk,
                    reply_markup=get_draft_review_keyboard(),
                )
            else:
                await update.message.reply_text(chunk)


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🤖 DevFlow AI Autonomous Commands\n\n"
        "/start - Start interacting with the agent\n"
        "/help - Show available commands\n"
        "/draft - Trigger an immediate research scan & review draft\n"
        "/approve - Publish the current pending draft\n"
        "/reject - Discard the current pending draft\n"
        "/chatid - Show this chat's ID"
    )


async def chat_id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message and update.effective_chat:
        await update.message.reply_text(
            f"This chat ID is `{update.effective_chat.id}`.",
            parse_mode="Markdown",
        )


async def draft_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.effective_chat:
        return

    chat_id = update.effective_chat.id
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        draft = await asyncio.to_thread(generate_daily_draft)
        chunks = split_message(draft)
        if not chunks:
            await update.message.reply_text(
                "The research workflow returned no publishable content. "
                "Please try /draft again."
            )
            return

        pending_drafts[chat_id] = "\n\n".join(chunks)
        await update.message.reply_text("📝 **Daily Draft Ready for Review:**", parse_mode="Markdown")
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await update.message.reply_text(
                    chunk,
                    reply_markup=get_draft_review_keyboard(),
                )
            else:
                await update.message.reply_text(chunk)
    except Exception as exc:
        logger.exception("Daily draft generation failed")
        await update.message.reply_text(
            f"I couldn't generate or send the draft: {exc}. Please try again."
        )


async def _execute_publish(
    context: ContextTypes.DEFAULT_TYPE,
    review_chat_id: int,
) -> bool:
    """Publish the pending draft to the destination channel and record to memory."""
    draft = pending_drafts.get(review_chat_id)
    if not draft:
        return False

    chunks = split_message(draft)
    if not chunks:
        pending_drafts.pop(review_chat_id, None)
        return False

    publish_chat_id = _publish_chat_id(review_chat_id)
    for chunk in chunks:
        await context.bot.send_message(chat_id=publish_chat_id, text=chunk)

    # Save published links to long-term memory to prevent future duplicates
    extracted_urls = re.findall(r"https?://[^\s\)\>]+", draft)
    for url in extracted_urls:
        record_published(
            title="Daily Broadcast Update",
            url=url,
            category="daily_post",
            content=draft[:400],
            channel_id=str(publish_chat_id),
        )

    del pending_drafts[review_chat_id]
    return True


async def approve_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.effective_chat:
        return

    review_chat_id = update.effective_chat.id
    if review_chat_id not in pending_drafts:
        await update.message.reply_text("There is no pending draft to publish.")
        return

    try:
        success = await _execute_publish(context, review_chat_id)
        if success:
            await update.message.reply_text("✅ Draft published successfully.")
        else:
            await update.message.reply_text(
                "The pending draft has no publishable content. Generate a new draft with /draft."
            )
    except Exception:
        logger.exception("Draft publishing failed")
        await update.message.reply_text(
            "I couldn't publish the draft. It is still pending."
        )


async def reject_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.effective_chat:
        return

    if pending_drafts.pop(update.effective_chat.id, None) is None:
        await update.message.reply_text("There is no pending draft to reject.")
        return
    await update.message.reply_text("🗑️ Draft discarded.")


async def handle_draft_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle interactive inline keyboard clicks for draft review."""
    query = update.callback_query
    if not query or not query.message or not query.data:
        return

    await query.answer()
    chat_id = query.message.chat_id
    action = query.data

    if action == "draft:approve":
        if chat_id not in pending_drafts:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("There is no pending draft to publish.")
            return

        try:
            success = await _execute_publish(context, chat_id)
            await query.edit_message_reply_markup(reply_markup=None)
            if success:
                await query.message.reply_text("✅ Draft published successfully to the channel!")
            else:
                await query.message.reply_text("Pending draft was empty. Please generate a new one.")
        except Exception as exc:
            logger.exception("Callback draft publish failed")
            await query.message.reply_text(f"Publishing failed: {exc}")

    elif action == "draft:reject":
        pending_drafts.pop(chat_id, None)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🗑️ Draft discarded.")

    elif action == "draft:regenerate":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🔄 Regenerating draft with fresh research...")
        try:
            draft = await asyncio.to_thread(generate_daily_draft)
            chunks = split_message(draft)
            if not chunks:
                await query.message.reply_text("Regeneration found no publishable items.")
                return

            pending_drafts[chat_id] = "\n\n".join(chunks)
            for i, chunk in enumerate(chunks):
                if i == len(chunks) - 1:
                    await query.message.reply_text(
                        chunk,
                        reply_markup=get_draft_review_keyboard(),
                    )
                else:
                    await query.message.reply_text(chunk)
        except Exception as exc:
            logger.exception("Regeneration failed")
            await query.message.reply_text(f"Regeneration failed: {exc}")


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    logger.info("Received message: %s", user_message)

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing",
        )

        response = await asyncio.to_thread(
            run_agent,
            user_message,
        )

        if not response:
            response = "I couldn't generate a response. Please try again."

        for chunk in split_message(response):
            await update.message.reply_text(chunk)

        logger.info("AI response sent successfully")

    except Exception:
        logger.exception("AI message processing failed")
        await update.message.reply_text(
            "Sorry! I encountered an error. Please try again."
        )


async def _post_init(app: Application) -> None:
    """Launch autonomous background scheduler on application startup."""
    from src.services.scheduler import start_autonomous_scheduler
    asyncio.create_task(start_autonomous_scheduler(app))


def create_application(token: str) -> Application:
    app = Application.builder().token(token).post_init(_post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chatid", chat_id_command))
    app.add_handler(CommandHandler("draft", draft_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("reject", reject_command))

    app.add_handler(CallbackQueryHandler(handle_draft_callback, pattern=r"^draft:"))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    return app
