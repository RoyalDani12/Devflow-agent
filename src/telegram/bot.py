import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.telegram.handlers import (
    _publish_chat_id,
    approve_command,
    chat_id_command,
    draft_command,
    handle_draft_callback,
    handle_message,
    help_command,
    pending_drafts,
    reject_command,
    start,
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


def create_application(token: str) -> Application:
    app = Application.builder().token(token).post_init(_post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chatid", chat_id_command))
    app.add_handler(CommandHandler("draft", draft_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("reject", reject_command))

    app.add_handler(CallbackQueryHandler(handle_draft_callback, pattern=r"^draft:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
