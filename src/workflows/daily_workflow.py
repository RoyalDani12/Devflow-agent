from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.tools.media_service import extract_media_image
from src.workflows.ai_news_workflow import generate_ai_news
from src.workflows.opportunities_workflow import generate_opportunities


class DailyContentState(TypedDict, total=False):
    news: str
    opportunities: str
    image_url: str
    draft: str


def create_daily_content(state: DailyContentState) -> DailyContentState:
    """Combine the independent news and opportunities outputs with visual media."""
    news = generate_ai_news()
    opportunities = generate_opportunities()
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


def generate_daily_draft() -> str:
    """Generate the combined daily draft without publishing it."""
    result = daily_workflow.invoke({})
    return result.get("draft", "")


def generate_daily_draft_payload() -> dict[str, str]:
    """Generate the daily draft text along with the best visual image."""
    result = daily_workflow.invoke({})
    draft = result.get("draft", "")
    img = result.get("image_url") or extract_media_image(draft, "daily")
    return {"text": draft, "image_url": img}
