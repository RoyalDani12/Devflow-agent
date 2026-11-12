
import logging
import sys

from src.config import get_required_setting
from src.telegram.bot import create_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Silence polling spam from httpx and httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("DevFlowAgent")

AGENT_BANNER = """
===================================================================
🤖 DEVFLOW AUTONOMOUS AI AGENT
===================================================================
🧠 Agent Brain: Groq (openai/gpt-oss-20b) with ReAct Loop
💾 Long-term Memory: Connected (SQLite: devflow_memory.db)
🌐 Research Tools: Devpost, Ethio-Scholarship, TechCrunch, Web Search
🔄 Autonomous Daemon: Auto-scanning for opportunities & AI news
===================================================================
"""


def main():
    token = get_required_setting("TELEGRAM_BOT_TOKEN")
    get_required_setting("GROQ_API_KEY")

    print(AGENT_BANNER)
    logger.info("DevFlow Autonomous Agent is initializing...")

    app = create_application(token)

    logger.info("Autonomous Agent is running and monitoring Telegram.")

    app.run_polling()


if __name__ == "__main__":
    main()
