import logging
from telegram import Bot, InlineKeyboardMarkup, LinkPreviewOptions

from src.telegram.card_manager import create_card, get_card_review_keyboard
from src.tools.media_service import (
    detect_section_category,
    extract_media_image,
    strip_markdown_asterisks,
)

logger = logging.getLogger("DevFlowMediaSender")


async def publish_content_with_media(bot: Bot, target_chat_id: int, text: str | list[str]) -> bool:
    """Publish each card as its OWN distinct message to the Telegram channel."""
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
            logger.warning("Publishing card message failed, falling back: %s", exc)
            await bot.send_message(chat_id=target_chat_id, text=clean_text)
    return True


async def send_draft_for_review(
    bot: Bot,
    target_chat_id: int,
    text: str | list[str],
    header: str = "",
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """Deliver each item as its OWN distinct message with individual approve/discard buttons."""
    from src.workflows.daily_workflow import split_draft_sections

    sections = split_draft_sections(text)
    if not sections:
        return False

    if header:
        try:
            await bot.send_message(chat_id=target_chat_id, text=header)
        except Exception:
            pass

    for i, section in enumerate(sections):
        card = create_card(section)
        link_options = (
            LinkPreviewOptions(url=card.image_url, prefer_large_media=True, show_above_text=True)
            if card.image_url
            else None
        )
        # Use card-specific keyboard unless caller specifically overrode it (e.g. tests)
        card_markup = reply_markup if reply_markup and i == len(sections) - 1 else get_card_review_keyboard(card.card_id)

        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text=card.text,
                link_preview_options=link_options,
                reply_markup=card_markup,
            )
        except Exception as exc:
            logger.warning("Draft preview card %d failed, falling back: %s", i, exc)
            await bot.send_message(
                chat_id=target_chat_id,
                text=card.text,
                reply_markup=card_markup,
            )
    return True
