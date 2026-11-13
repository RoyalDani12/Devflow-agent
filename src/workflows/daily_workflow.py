import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.database.memory import record_opportunity
from src.tools.media_service import detect_section_category, extract_media_image, strip_markdown_asterisks
from src.workflows.ai_news_workflow import generate_ai_news
from src.workflows.opportunities_workflow import generate_opportunities


class DailyContentState(TypedDict, total=False):
    news: str
    opportunities: str
    image_url: str
    draft: str


def format_journal_card(text: str) -> str:
    """Ensure a card has a clean journalistic heading and no asterisks."""
    clean = strip_markdown_asterisks(text).strip()
    if not clean:
        return ""
    cat = detect_section_category(clean)
    if cat == "ai_news":
        if "📰" not in clean and "AI & TECH" not in clean:
            clean = f"📰 AI & TECH JOURNAL DISPATCH\n{clean}"
    elif cat == "opportunities":
        if "🎓" not in clean and "OPPORTUNITY" not in clean:
            clean = f"🎓 GLOBAL OPPORTUNITY DISPATCH | ETHIOPIA ELIGIBLE\n{clean}"
    return clean


def split_draft_sections(draft_data: str | list[str]) -> list[str]:
    """Split draft into distinct, individual card messages for independent review."""
    if isinstance(draft_data, list):
        items = []
        for s in draft_data:
            items.extend(split_draft_sections(s))
        return items

    clean = strip_markdown_asterisks(draft_data).strip()
    if not clean:
        return []

    if "===ITEM===" in clean:
        raw_items = [p.strip() for p in clean.split("===ITEM===") if p.strip()]
        return [format_journal_card(it) for it in raw_items if len(it) > 15]

    if "===SECTION===" in clean:
        raw_items = [p.strip() for p in clean.split("===SECTION===") if p.strip()]
        return [format_journal_card(it) for it in raw_items if len(it) > 15]

    parts = re.split(r"\n\n+(?=(?:📰|🎓|🚀|🎯|🌟|⚡))", clean)
    filtered = [format_journal_card(p) for p in parts if len(p.strip()) > 15]
    return filtered if filtered else [format_journal_card(clean)]


def create_daily_content(state: DailyContentState) -> DailyContentState:
    """Combine the independent news and opportunities outputs with visual media."""
    news = strip_markdown_asterisks(generate_ai_news())
    opportunities = strip_markdown_asterisks(generate_opportunities())
    combined_text = f"{news}\n\n{opportunities}".strip()
    image_url = extract_media_image(combined_text, fallback_category="daily")
    return {
        "news": news,
        "opportunities": opportunities,
        "image_url": image_url,
        "draft": combined_text,
    }


def build_daily_workflow():
    """Build the orchestration workflow for the daily channel draft."""
    workflow = StateGraph(DailyContentState)
    workflow.add_node("create_daily_content", create_daily_content)
    workflow.add_edge(START, "create_daily_content")
    workflow.add_edge("create_daily_content", END)
    return workflow.compile()


daily_workflow = build_daily_workflow()


def generate_daily_draft_sections() -> list[str]:
    """Generate independent, separate items for AI News and Developer Opportunities."""
    result = daily_workflow.invoke({})
    draft = result.get("draft", "")
    sections = split_draft_sections(draft)
    for section in sections:
        for url in re.findall(r"https?://[^\s\)\>]+", section):
            record_opportunity(name="Draft item", url=url, status="presented")
    return sections


def generate_daily_draft() -> str:
    """Generate the combined daily draft, recording items to avoid repetition."""
    result = daily_workflow.invoke({})
    draft = strip_markdown_asterisks(result.get("draft", ""))
    for url in re.findall(r"https?://[^\s\)\>]+", draft):
        record_opportunity(name="Draft item", url=url, status="presented")
    return draft
