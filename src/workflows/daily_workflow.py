import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.database.memory import record_opportunity
from src.tools.media_service import extract_media_image, strip_markdown_asterisks
from src.workflows.ai_news_workflow import generate_ai_news
from src.workflows.opportunities_workflow import generate_opportunities


class DailyContentState(TypedDict, total=False):
    news: str
    opportunities: str
    image_url: str
    draft: str


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


def split_draft_sections(draft_data: str | list[str]) -> list[str]:
    """Split draft into distinct section messages for independent delivery."""
    if isinstance(draft_data, list):
        return [strip_markdown_asterisks(s) for s in draft_data if s and s.strip()]
    if "\n\n===SECTION===\n\n" in draft_data:
        return [strip_markdown_asterisks(s) for s in draft_data.split("\n\n===SECTION===\n\n") if s.strip()]
    if "🎯" in draft_data and "🚀" in draft_data:
        parts = draft_data.split("🎯", 1)
        return [strip_markdown_asterisks(parts[0]), strip_markdown_asterisks("🎯" + parts[1])]
    return [strip_markdown_asterisks(draft_data)] if draft_data and draft_data.strip() else []


def generate_daily_draft_sections() -> list[str]:
    """Generate independent, separate sections for AI News and Developer Opportunities."""
    news = strip_markdown_asterisks(generate_ai_news())
    opportunities = strip_markdown_asterisks(generate_opportunities())

    sections = [s for s in (news, opportunities) if s and s.strip()]
    for section in sections:
        for url in re.findall(r"https?://[^\s\)\>]+", section):
            record_opportunity(name="Draft item", url=url, status="presented")
    return sections


def generate_daily_draft() -> str:
    """Generate the combined daily draft with clear section separators to prevent repetition."""
    result = daily_workflow.invoke({})
    draft = strip_markdown_asterisks(result.get("draft", ""))
    for url in re.findall(r"https?://[^\s\)\>]+", draft):
        record_opportunity(name="Draft item", url=url, status="presented")
    return draft


def generate_daily_draft_payload() -> dict[str, str]:
    """Generate the daily draft text along with the best visual image."""
    result = daily_workflow.invoke({})
    draft = strip_markdown_asterisks(result.get("draft", ""))
    img = result.get("image_url") or extract_media_image(draft, "daily")
    return {"text": draft, "image_url": img}
