import logging
from telegram import Bot, InlineKeyboardMarkup

from src.tools.media_service import build_caption_and_body, extract_media_image

logger = logging.getLogger("DevFlowMediaSender")


async def publish_content_with_media(bot: Bot, target_chat_id: int, text: str) -> bool:
    """Publish content with an image banner to Telegram channel, falling back gracefully to text."""
    from src.telegram.bot import split_message

    image_url = extract_media_image(text, fallback_category="daily")
    caption, body_chunks = build_caption_and_body(text)

    try:
        if image_url:
            await bot.send_photo(chat_id=target_chat_id, photo=image_url, caption=caption)
            for chunk in body_chunks:
                await bot.send_message(chat_id=target_chat_id, text=chunk)
            return True
    except Exception as exc:
        logger.warning("send_photo failed during publish, falling back to text: %s", exc)

    # Fallback to pure text messages
    for chunk in split_message(text):
        await bot.send_message(chat_id=target_chat_id, text=chunk)
    return True


async def send_draft_for_review(
    bot: Bot,
    target_chat_id: int,
    text: str,
    header: str = "📝 **Daily Draft Ready for Review:**",
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """Send draft preview with media banner and review keyboard."""
    from src.telegram.bot import get_draft_review_keyboard, split_message

    markup = reply_markup or get_draft_review_keyboard()
    image_url = extract_media_image(text, fallback_category="daily")
    caption, body_chunks = build_caption_and_body(text)

    if header:
        try:
            await bot.send_message(chat_id=target_chat_id, text=header, parse_mode="Markdown")
        except Exception:
            await bot.send_message(chat_id=target_chat_id, text=header)

    try:
        if image_url:
            card_markup = markup if not body_chunks else None
            await bot.send_photo(
                chat_id=target_chat_id,
                photo=image_url,
                caption=caption,
                reply_markup=card_markup,
            )
            for i, chunk in enumerate(body_chunks):
                chunk_markup = markup if i == len(body_chunks) - 1 else None
                await bot.send_message(chat_id=target_chat_id, text=chunk, reply_markup=chunk_markup)
            return True
    except Exception as exc:
        logger.warning("send_photo failed during draft preview, falling back to text: %s", exc)

    chunks = split_message(text)
    for i, chunk in enumerate(chunks):
        chunk_markup = markup if i == len(chunks) - 1 else None
        await bot.send_message(chat_id=target_chat_id, text=chunk, reply_markup=chunk_markup)
    return True
