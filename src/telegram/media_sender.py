import logging
from telegram import Bot, InlineKeyboardMarkup, LinkPreviewOptions

from src.tools.media_service import extract_media_image

logger = logging.getLogger("DevFlowMediaSender")


async def publish_content_with_media(bot: Bot, target_chat_id: int, text: str) -> bool:
    """Publish content as ONE single message with an image banner to the Telegram channel."""
    from src.telegram.bot import split_message

    image_url = extract_media_image(text, fallback_category="daily")
    clean_text = text.strip()

    if len(clean_text) <= 4000:
        try:
            link_options = (
                LinkPreviewOptions(url=image_url, prefer_large_media=True, show_above_text=True)
                if image_url
                else None
            )
            await bot.send_message(
                chat_id=target_chat_id,
                text=clean_text,
                link_preview_options=link_options,
            )
            return True
        except Exception as exc:
            logger.warning("Publishing single message with LinkPreviewOptions failed: %s", exc)
            await bot.send_message(chat_id=target_chat_id, text=clean_text)
            return True

    for chunk in split_message(clean_text):
        await bot.send_message(chat_id=target_chat_id, text=chunk)
    return True


async def send_draft_for_review(
    bot: Bot,
    target_chat_id: int,
    text: str,
    header: str = "",
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """Deliver the draft preview as ONE single message with banner and inline buttons."""
    from src.telegram.bot import get_draft_review_keyboard, split_message

    markup = reply_markup or get_draft_review_keyboard()
    image_url = extract_media_image(text, fallback_category="daily")
    message_text = f"{header}\n\n{text}".strip() if header else text.strip()

    if len(message_text) <= 4000:
        try:
            link_options = (
                LinkPreviewOptions(url=image_url, prefer_large_media=True, show_above_text=True)
                if image_url
                else None
            )
            await bot.send_message(
                chat_id=target_chat_id,
                text=message_text,
                link_preview_options=link_options,
                reply_markup=markup,
            )
            return True
        except Exception as exc:
            logger.warning("Draft preview single message failed, falling back: %s", exc)
            await bot.send_message(
                chat_id=target_chat_id,
                text=message_text,
                reply_markup=markup,
            )
            return True

    chunks = split_message(message_text)
    for i, chunk in enumerate(chunks):
        chunk_markup = markup if i == len(chunks) - 1 else None
        await bot.send_message(chat_id=target_chat_id, text=chunk, reply_markup=chunk_markup)
    return True
