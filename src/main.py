
import logging

from src.config import get_required_setting
from src.telegram.bot import create_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    token = get_required_setting("TELEGRAM_BOT_TOKEN")
    get_required_setting("GROQ_API_KEY")

    app = create_application(token)

    logger.info("DevFlow AI is running!")

    app.run_polling()


if __name__ == "__main__":
    main()
