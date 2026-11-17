import logging
from telegram import Bot, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.error import BadRequest, ChatMigrated, Forbidden

from src.telegram.card_manager import create_card, get_card_review_keyboard
from src.tools.media_service import (
    detect_section_category,
    extract_media_image,
    strip_markdown_asterisks,
)

logger = logging.getLogger("DevFlowMediaSender")

_CHAT_NOT_FOUND_HINT = (
    "\n\n⚠️  Could not find the publish channel.\n\n"
    "Fix: Send /chatid to get your channel ID, then add it to .env:\n"
    "TELEGRAM_PUBLISH_CHAT_ID=-100xxxxxxxxxx\n\n"
    "For now, messages are delivered here (your DM) instead."
)


async def _send_with_fallback(bot: Bot, chat_id, text: str, **kwargs) -> bool:
    """Try to send with link preview; on failure try plain text; on Chat not found raise clearly."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
    except (BadRequest, Forbidden, ChatMigrated) as exc:
        err = str(exc).lower()
        if "chat not found" in err or "not found" in err:
            raise  # Let callers handle with helpful message
        # Other errors (e.g. link preview failed) — retry plain
        logger.warning("Publishing message failed, retrying plain: %s", exc)
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception as exc2:
            logger.error("Plain fallback also failed: %s", exc2)
            return False
    except Exception as exc:
        logger.warning("Publishing card message failed, falling back: %s", exc)
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception:
            return False


async def publish_content_with_media(
    bot: Bot,
    target_chat_id,
    text: str | list[str],
    review_chat_id=None,
) -> bool:
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
            await _send_with_fallback(
                bot, target_chat_id, clean_text,
                link_preview_options=link_options,
            )
        except (BadRequest, Forbidden) as exc:
            if "chat not found" in str(exc).lower() or "not found" in str(exc).lower():
                logger.error("Channel not found (ID: %s). Check TELEGRAM_PUBLISH_CHAT_ID in .env", target_chat_id)
                # Deliver to review chat with setup hint if we know it
                fallback = review_chat_id or target_chat_id
                try:
                    await bot.send_message(
                        chat_id=fallback,
                        text=clean_text + _CHAT_NOT_FOUND_HINT,
                    )
                except Exception:
                    pass
            else:
                raise
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
        card_markup = (
            reply_markup
            if reply_markup and i == len(sections) - 1
            else get_card_review_keyboard(card.card_id)
        )

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
