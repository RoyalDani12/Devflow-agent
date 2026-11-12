
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.agents.devflow_agent import run_agent

logger = logging.getLogger(__name__)
MAX_TELEGRAM_MESSAGE_LENGTH = 4000


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

        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    if remaining:
        chunks.append(remaining)

    return chunks


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "Hey! 👋 Welcome to DevFlow AI!\n\n"
        "I'm your AI developer assistant.\n\n"
        "🚀 AI news\n"
        "💻 Developer tips\n"
        "🎯 Tech opportunities\n\n"
        "Send me a message to start chatting!"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🤖 DevFlow AI Commands\n\n"
        "/start - Start the bot\n"
        "/help - Show available commands"
    )


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


def create_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    return app
