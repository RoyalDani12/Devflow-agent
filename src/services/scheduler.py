import asyncio
import logging
import os
import re

from telegram import Bot

from src.database.memory import record_opportunity, record_published
from src.telegram.bot import (
    _publish_chat_id,
    get_draft_review_keyboard,
    pending_drafts,
    split_message,
)
from src.workflows.daily_workflow import generate_daily_draft

logger = logging.getLogger("DevFlowScheduler")
DEFAULT_INTERVAL_SECONDS = 86400  # 24 hours
latest_cached_briefing: str = ""
active_admin_chat_id: int | None = None


def set_active_admin_chat(chat_id: int) -> None:
    """Dynamically register the admin chat ID when a user interacts with the bot."""
    global active_admin_chat_id
    active_admin_chat_id = chat_id


def get_active_admin_chat() -> int | None:
    """Get the active review chat ID from env or dynamic registration."""
    global active_admin_chat_id
    if active_admin_chat_id:
        return active_admin_chat_id
    env_id = os.getenv("TELEGRAM_REVIEW_CHAT_ID") or os.getenv("TELEGRAM_PUBLISH_CHAT_ID")
    if env_id:
        try:
            return int(env_id)
        except ValueError:
            pass
    return None


async def run_autonomous_scan_cycle(bot: Bot | None = None, review_chat_id: int | None = None) -> bool:
    """Execute one autonomous discovery, verification, and notification cycle."""
    global latest_cached_briefing
    logger.info("🤖 Autonomous Agent: Starting research scan cycle...")

    try:
        draft = await asyncio.to_thread(generate_daily_draft)
        chunks = split_message(draft)
        if not chunks:
            logger.info("🤖 Autonomous Agent: No new high-impact items verified today. Standing by.")
            return False

        latest_cached_briefing = draft
        target_chat = review_chat_id or get_active_admin_chat()

        # Save discovered links into memory
        urls = re.findall(r"https?://[^\s\)\>]+", draft)
        for url in urls:
            record_opportunity(
                name="Discovered in Autonomous Scan",
                url=url,
                deadline="Verified future deadline",
                eligibility="Confirmed open",
                status="verified",
            )

        logger.info("🤖 Autonomous Agent: Scan complete! Found %d publishable chunks & %d links.", len(chunks), len(urls))

        if not bot or not target_chat:
            logger.info("🤖 Autonomous Agent: Research briefing cached. Waiting for Telegram admin connection to deliver.")
            return True

        auto_publish = os.getenv("AUTO_PUBLISH", "false").lower() in {"1", "true", "yes"}

        if auto_publish:
            publish_chat_id = _publish_chat_id(target_chat)
            logger.info("🤖 Autonomous Agent: AUTO_PUBLISH=true. Broadcasting to %s", publish_chat_id)
            for chunk in chunks:
                await bot.send_message(chat_id=publish_chat_id, text=chunk)

            for url in urls:
                record_published(
                    title="Autonomous Daily Broadcast",
                    url=url,
                    category="daily_post",
                    content=draft[:400],
                    channel_id=str(publish_chat_id),
                )
            return True

        # Send proactive briefing with interactive review buttons to admin
        pending_drafts[target_chat] = "\n\n".join(chunks)
        await bot.send_message(
            chat_id=target_chat,
            text="🤖 **DevFlow Autonomous Briefing Ready for Review**\n\n"
            "I completed today's autonomous research scan. Review the draft below:",
            parse_mode="Markdown",
        )
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await bot.send_message(
                    chat_id=target_chat,
                    text=chunk,
                    reply_markup=get_draft_review_keyboard(),
                )
            else:
                await bot.send_message(chat_id=target_chat, text=chunk)

        logger.info("🤖 Autonomous Agent: Briefing successfully delivered to admin chat %s", target_chat)
        return True

    except Exception as exc:
        logger.exception("Autonomous scan cycle failed: %s", exc)
        return False


async def start_autonomous_scheduler(app, interval_seconds: int = DEFAULT_INTERVAL_SECONDS):
    """Background task: runs an immediate scan cycle on launch, then repeats on interval."""
    # Small initial pause for Telegram connection to establish
    await asyncio.sleep(2)
    logger.info("🚀 Launching initial autonomous research cycle on agent startup...")
    await run_autonomous_scan_cycle(app.bot)

    while True:
        await asyncio.sleep(interval_seconds)
        logger.info("⏰ Autonomous Agent: Waking up for scheduled daily research scan...")
        await run_autonomous_scan_cycle(app.bot)
