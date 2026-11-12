from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response


class AINewsState(TypedDict, total=False):
    news: str


AI_NEWS_PROMPT = f"""Create a Telegram-ready AI news section for developers.
The current date is {date.today().isoformat()}. Include no more than two recent
AI or technology news items.

For each item:
- Use current, real information from a reliable official source.
- Include the publication date and a direct source URL.
- Summarize the important development concisely.
- Never invent a story, date, or source.

If no news can be verified, say that clearly. Do not include opportunities,
developer tips, interview questions, or claims that anything was published."""


def create_ai_news(state: AINewsState) -> AINewsState:
    """Generate a separate, reviewable AI news section."""
    return {"news": generate_response(AI_NEWS_PROMPT)}


def build_ai_news_workflow():
    """Build and compile the AI news workflow."""
    workflow = StateGraph(AINewsState)
    workflow.add_node("create_ai_news", create_ai_news)
    workflow.add_edge(START, "create_ai_news")
    workflow.add_edge("create_ai_news", END)
    return workflow.compile()


ai_news_workflow = build_ai_news_workflow()


def generate_ai_news() -> str:
    """Generate the daily AI news section."""
    result = ai_news_workflow.invoke({})
    return result.get("news", "")
