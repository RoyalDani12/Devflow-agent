
import os
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "Hey! 👋 Welcome to DevFlow AI!\n\n"
        "I'm your developer assistant.\n\n"
        "I'll bring you:\n"
        "🚀 AI news\n"
        "💻 Developer tips\n"
        "🎯 Tech opportunities\n\n"
        "Something exciting is coming!"
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


def main():
    if not TOKEN:
        raise ValueError("Telegram token missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("DevFlow AI is running!")

    app.run_polling()


if __name__ == "__main__":
    main()
