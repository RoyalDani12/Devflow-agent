from dataclasses import dataclass
import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.tools.media_service import detect_section_category, extract_media_image, strip_markdown_asterisks


@dataclass
class DraftCard:
    card_id: str
    category: str
    text: str
    image_url: str | None = None
    status: str = "pending"


# Global store for pending reviewable cards
pending_cards: dict[str, DraftCard] = {}


def create_card(text: str, category: str | None = None) -> DraftCard:
    """Create and register a new reviewable draft card."""
    clean_text = strip_markdown_asterisks(text).strip()
    detected_cat = category or detect_section_category(clean_text)
    image_url = extract_media_image(clean_text, fallback_category=detected_cat)
    card_id = f"c_{uuid.uuid4().hex[:8]}"

    card = DraftCard(
        card_id=card_id,
        category=detected_cat,
        text=clean_text,
        image_url=image_url,
        status="pending",
    )
    pending_cards[card_id] = card
    return card


def get_card(card_id: str) -> DraftCard | None:
    """Retrieve a pending card by id."""
    return pending_cards.get(card_id)


def pop_card(card_id: str) -> DraftCard | None:
    """Remove and return a card from pending store."""
    return pending_cards.pop(card_id, None)


def clear_all_cards() -> None:
    """Clear all pending cards."""
    pending_cards.clear()


def get_all_pending_cards() -> list[DraftCard]:
    """Return all currently pending cards."""
    return [c for c in pending_cards.values() if c.status == "pending"]


def get_card_review_keyboard(card_id: str) -> InlineKeyboardMarkup:
    """Create interactive approval buttons specifically for this individual card."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve & Publish", callback_data=f"card:approve:{card_id}"),
            InlineKeyboardButton("❌ Discard", callback_data=f"card:reject:{card_id}"),
        ]
    ])
