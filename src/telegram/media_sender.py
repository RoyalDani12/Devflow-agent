import logging
from telegram import Bot, InlineKeyboardMarkup, LinkPreviewOptions

from src.tools.media_service import (
    detect_section_category,
    extract_media_image,
    strip_markdown_asterisks,
)

logger = logging.getLogger("DevFlowMediaSender")


async def publish_content_with_media(bot: Bot, target_chat_id: int, text: str | list[str]) -> bool:
    """Publish each section as its OWN distinct message to the Telegram channel."""
    from src.workflows.daily_workflow import split_draft_sections

    sections = split_draft_sections(text)
    if not sections:
        return False

    for section in sections:
        clean_text = strip_markdown_asterisks(section)
        category = detect_section_category(clean_text)
        image_url = extract_media_image(clean_text, fallback_category=category)
        link_options = (
            LinkPreviewOptions(url=image_url, prefer_large_media=True, show_above_text=True)
            if image_url
            else None
        )
        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text=clean_text,
                link_preview_options=link_options,
            )
        except Exception as exc:
            logger.warning("Publishing section message failed, falling back: %s", exc)
            await bot.send_message(chat_id=target_chat_id, text=clean_text)
    return True


async def send_draft_for_review(
    bot: Bot,
    target_chat_id: int,
    text: str | list[str],
    header: str = "",
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """Deliver each section as its OWN distinct message with category banner and buttons."""
    from src.telegram.bot import get_draft_review_keyboard
    from src.workflows.daily_workflow import split_draft_sections

    markup = reply_markup or get_draft_review_keyboard()
    sections = split_draft_sections(text)
    if not sections:
        return False

    if header:
        try:
            await bot.send_message(chat_id=target_chat_id, text=header)
        except Exception:
            pass

    for i, section in enumerate(sections):
        clean_text = strip_markdown_asterisks(section)
        category = detect_section_category(clean_text)
        image_url = extract_media_image(clean_text, fallback_category=category)
        link_options = (
            LinkPreviewOptions(url=image_url, prefer_large_media=True, show_above_text=True)
            if image_url
            else None
        )
        card_markup = markup if i == len(sections) - 1 else None

        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text=clean_text,
                link_preview_options=link_options,
                reply_markup=card_markup,
            )
        except Exception as exc:
            logger.warning("Draft preview section %d failed, falling back: %s", i, exc)
            await bot.send_message(
                chat_id=target_chat_id,
                text=clean_text,
                reply_markup=card_markup,
            )
    return True
