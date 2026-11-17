import hashlib
import logging
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger("DevFlowMedia")

DEFAULT_BANNERS = {
    "daily": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1200&q=80",
    "ai_news": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80",
    "opportunities": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
    "hackathons": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
    "scholarships": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80",
}

TOPIC_POOLS: dict[str, list[str]] = {
    "chips": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=1200&q=80",
    ],
    "robotics": [
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1546776310-eef45dd6d63c?auto=format&fit=crop&w=1200&q=80",
    ],
    "ai_models": [
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80",
    ],
    "coding": [
        "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1200&q=80",
    ],
    "scholarships": [
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1200&q=80",
    ],
    "hackathons": [
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1200&q=80",
    ],
    "fellowships": [
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1200&q=80",
    ],
}

URL_IMAGE_CACHE: dict[str, str] = {}
IMAGE_URL_PATTERN = re.compile(r"https?://[^\s\)\>\"']+\.(?:png|jpe?g|webp|gif)(?:\?[^\s\)\>\"']*)?", re.IGNORECASE)
DEVPOST_CDN_PATTERN = re.compile(r"https?://d112y698adiu2z\.cloudfront\.net/[^\s\)\>\"']+", re.IGNORECASE)


def register_url_image(url: str, img_url: str) -> None:
    """Store a verified image URL associated with a source page."""
    if url and img_url and img_url.startswith("http"):
        URL_IMAGE_CACHE[url.strip()] = img_url.strip()


def extract_og_image_from_html(html: str) -> str | None:
    """Extract OpenGraph or Twitter card preview image from HTML text."""
    for pattern in (
        r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\s\"\']+)[\"\']',
        r'<meta[^>]+content=[\"\']([^\s\"\']+)[\"\'][^>]+property=[\"\']og:image[\"\']',
        r'<meta[^>]+name=[\"\']twitter:image[\"\'][^>]+content=[\"\']([^\s\"\']+)[\"\']',
    ):
        m = re.search(pattern, html, re.IGNORECASE)
        if m and m.group(1).startswith("http"):
            return m.group(1)
    return None


def get_category_banner(category: str = "daily", text_seed: str = "") -> str:
    """Return a diverse high-resolution banner URL rotated by content seed."""
    pool = TOPIC_POOLS.get(category)
    if pool:
        idx = int(hashlib.md5(text_seed.encode("utf-8")).hexdigest(), 16) % len(pool) if text_seed else 0
        return pool[idx]
    return DEFAULT_BANNERS.get(category, DEFAULT_BANNERS["daily"])


def strip_markdown_asterisks(text: str) -> str:
    """Remove all markdown asterisks while preserving clean readability."""
    return re.sub(r"\*{1,3}", "", text).strip() if text else ""


def detect_section_category(text: str) -> str:
    """Detect specific thematic category to select the most relevant visual banner."""
    lower = text.lower()
    if any(k in lower for k in ["scholarship", "masters", "phd", "university", "student", "tuition"]):
        return "scholarships"
    if any(k in lower for k in ["hackathon", "devpost", "challenge", "prize"]):
        return "hackathons"
    if any(k in lower for k in ["fellowship", "internship", "grant", "programme", "forum"]):
        return "fellowships"
    if any(k in lower for k in ["chip", "nvidia", "gpu", "semiconductor", "hardware"]):
        return "chips"
    if any(k in lower for k in ["robot", "robotics", "autonomous"]):
        return "robotics"
    if any(k in lower for k in ["code", "developer tool", "framework", "python", "software"]):
        return "coding"
    return "ai_models" if "ai" in lower or "model" in lower else "daily"


def extract_media_image(text: str, fallback_category: str = "daily") -> str:
    """Extract an authentic article image or select a content-matching diverse banner."""
    if not text:
        return get_category_banner(fallback_category)

    cdn_match = DEVPOST_CDN_PATTERN.search(text)
    if cdn_match:
        return cdn_match.group(0)

    img_match = IMAGE_URL_PATTERN.search(text)
    if img_match:
        return img_match.group(0)

    # Check cached real article images
    for url in re.findall(r"https?://[^\s\)\>]+", text):
        cached = URL_IMAGE_CACHE.get(url.strip())
        if cached:
            return cached

    if fallback_category != "daily":
        return get_category_banner(fallback_category)

    topic = detect_section_category(text)
    return get_category_banner(topic, text_seed=text[:80])


def build_caption_and_body(text: str, max_caption_len: int = 1000) -> tuple[str, list[str]]:
    """Format text for Telegram send_photo caption (<=1024 chars) and subsequent body chunks."""
    from src.telegram.bot import split_message

    cleaned = strip_markdown_asterisks(text)
    if len(cleaned) <= max_caption_len:
        return cleaned, []

    split_pos = cleaned.rfind("\n\n", 0, max_caption_len)
    if split_pos <= 0:
        split_pos = cleaned.rfind("\n", 0, max_caption_len)
    if split_pos <= 0:
        split_pos = max_caption_len

    caption = cleaned[:split_pos].strip()
    remaining = cleaned[split_pos:].strip()
    body_chunks = split_message(remaining) if remaining else []
    return caption, body_chunks
