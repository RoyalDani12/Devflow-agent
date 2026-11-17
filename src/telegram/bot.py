import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden, NetworkError, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.telegram.handlers import (
    _publish_chat_id,
    approve_command,
    chat_id_command,
    draft_command,
    handle_card_callback,
    handle_draft_callback,
    help_command,
    pending_drafts,
    reject_command,
    start,
)
from src.telegram.settings_handlers import (
    handle_message,
    handle_settings_callback,
    settings_command,
)

logger = logging.getLogger(__name__)
MAX_TELEGRAM_MESSAGE_LENGTH = 4000


def split_message(message: str) -> list[str]:
    """Split a response into chunks that Telegram can accept."""
    chunks = []
    remaining = message

    while len(remaining) > MAX_TELEGRAM_MESSAGE_LENGTH:
        split_at = remaining.rfind("\n", 0, MAX_TELEGRAM_MESSAGE_LENGTH)
        if split_at <= 0:
            split_at = remaining.rfind(" ", 0, MAX_TELEGRAM_MESSAGE_LENGTH)
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


async def _post_init(app: Application) -> None:
    """Launch autonomous background scheduler on application startup."""
    from src.services.scheduler import start_autonomous_scheduler
    asyncio.create_task(start_autonomous_scheduler(app))


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler — logs all unhandled exceptions cleanly."""
    err = context.error
    if isinstance(err, (NetworkError,)):
        logger.warning("Network error (transient): %s", err)
        return
    if isinstance(err, (BadRequest, Forbidden)):
        if "chat not found" in str(err).lower():
            logger.error(
                "Chat not found — TELEGRAM_PUBLISH_CHAT_ID in .env is wrong or bot is not "
                "an admin in the channel. Send /chatid in your DM to get the correct ID."
            )
            if isinstance(update, Update) and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "⚠️  Channel not found!\n\n"
                        "The bot cannot find your publish channel.\n\n"
                        "Steps to fix:\n"
                        "1. Send /chatid to get your channel's numeric ID\n"
                        "2. Add this bot as Admin in your channel (Post Messages permission)\n"
                        "3. Update .env:  TELEGRAM_PUBLISH_CHAT_ID=-100xxxxxxxxxx\n"
                        "4. Restart the bot\n\n"
                        "Until then, approved cards will be delivered here in this DM."
                    )
                except Exception:
                    pass
            return
        logger.error("Telegram API error: %s", err)
        return
    logger.exception("Unhandled exception in update handler", exc_info=err)


def create_application(token: str) -> Application:
    app = Application.builder().token(token).post_init(_post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chatid", chat_id_command))
    app.add_handler(CommandHandler("draft", draft_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("reject", reject_command))
    app.add_handler(CommandHandler("settings", settings_command))

    app.add_handler(CallbackQueryHandler(handle_card_callback, pattern=r"^card:"))
    app.add_handler(CallbackQueryHandler(handle_draft_callback, pattern=r"^draft:"))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern=r"^settings:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(_error_handler)

    return app
