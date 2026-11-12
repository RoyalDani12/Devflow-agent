from functools import wraps
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

from src.database.memory import get_stored_admin_id, set_stored_admin_id

logger = logging.getLogger("DevFlowAuth")


def get_owner_user_id() -> int | None:
    """Retrieve the authorized owner user ID from env or persistent memory."""
    env_admin = os.getenv("TELEGRAM_ADMIN_ID") or os.getenv("ADMIN_USER_ID")
    if env_admin:
        try:
            return int(env_admin)
        except ValueError:
            pass
    return get_stored_admin_id()


def is_authorized_user(user_id: int) -> bool:
    """Check if the requesting user is the authenticated owner."""
    owner_id = get_owner_user_id()
    if owner_id is None:
        # First contact claims ownership
        set_stored_admin_id(user_id)
        logger.info("Owner locked to user ID: %s", user_id)
        return True
    return user_id == owner_id


def require_admin(func):
    """Decorator that blocks unauthorized Telegram users."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or not is_authorized_user(user.id):
            user_id = user.id if user else "Unknown"
            logger.warning("Blocked unauthorized request from user %s", user_id)
            if update.message:
                await update.message.reply_text(
                    "⛔ Access Denied: This is a private autonomous AI agent reserved exclusively for the owner."
                )
            elif update.callback_query:
                await update.callback_query.answer("⛔ Access Denied: Unauthorized.", show_alert=True)
            return None
        return await func(update, context, *args, **kwargs)

    return wrapper
