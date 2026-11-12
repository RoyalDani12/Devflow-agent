from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.workflows.ai_news_workflow import generate_ai_news
from src.workflows.opportunities_workflow import generate_opportunities


class DailyContentState(TypedDict, total=False):
    news: str
    opportunities: str
    draft: str


def create_daily_content(state: DailyContentState) -> DailyContentState:
    """Combine the independent news and opportunities outputs."""
    news = generate_ai_news()
    opportunities = generate_opportunities()
    return {
        "news": news,
        "opportunities": opportunities,
        "draft": f"{news}\n\n{opportunities}",
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
