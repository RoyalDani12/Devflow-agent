import re

DEFAULT_BANNERS = {
    "daily": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1200&q=80",
    "ai_news": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80",
    "opportunities": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
    "hackathons": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
    "scholarships": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80",
}

IMAGE_URL_PATTERN = re.compile(
    r"https?://[^\s\)\>\"']+\.(?:png|jpe?g|webp|gif)(?:\?[^\s\)\>\"']*)?",
    re.IGNORECASE,
)
DEVPOST_CDN_PATTERN = re.compile(
    r"https?://d112y698adiu2z\.cloudfront\.net/[^\s\)\>\"']+",
    re.IGNORECASE,
)


def get_category_banner(category: str = "daily") -> str:
    """Return a high-resolution, relevant banner URL for a content category."""
    return DEFAULT_BANNERS.get(category, DEFAULT_BANNERS["daily"])


def extract_media_image(text: str, fallback_category: str = "daily") -> str:
    """Extract an explicit image URL from text, or return category-specific banner."""
    if not text:
        return get_category_banner(fallback_category)

    cdn_match = DEVPOST_CDN_PATTERN.search(text)
    if cdn_match:
        return cdn_match.group(0)

    img_match = IMAGE_URL_PATTERN.search(text)
    if img_match:
        return img_match.group(0)

    return get_category_banner(fallback_category)


def build_caption_and_body(text: str, max_caption_len: int = 1000) -> tuple[str, list[str]]:
    """Format text for Telegram send_photo caption (<=1024 chars) and subsequent body chunks."""
    from src.telegram.bot import split_message

    text = text.strip()
    if len(text) <= max_caption_len:
        return text, []

    # Find clean paragraph break within limit
    split_pos = text.rfind("\n\n", 0, max_caption_len)
    if split_pos <= 0:
        split_pos = text.rfind("\n", 0, max_caption_len)
    if split_pos <= 0:
        split_pos = max_caption_len

    caption = text[:split_pos].strip()
    remaining = text[split_pos:].strip()
    body_chunks = split_message(remaining) if remaining else []
    return caption, body_chunks
