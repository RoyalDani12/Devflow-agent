from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response
from src.tools.web_research import collect_page_evidence


class AINewsState(TypedDict, total=False):
    evidence: str
    news: str


AI_NEWS_PROMPT = f"""Create a Telegram-ready AI and technology news section for
developers. The current date is {date.today().isoformat()}.
Include no more than two recent, high-impact items. Do not limit coverage to AI models.

For each item, use only the verified page evidence supplied below:
- Identify the category: model, product, research, robotics, chips or
  infrastructure, developer tool, startup/funding, policy/safety, or major
  industry adoption.
- Include the publication date and a direct source URL.
- Explain what changed, what is genuinely new or different, what it adds
  compared with earlier approaches, and why developers should care.
- Distinguish an original announcement, research result, product release,
  funding event, policy change, and opinion article.
- Never invent a story, date, or source.

If the evidence is empty or insufficient, say that clearly. Do not include opportunities,
developer tips, interview questions, or claims that anything was published."""


def create_ai_news(state: AINewsState) -> AINewsState:
    """Generate a separate, reviewable AI news section."""
    prompt = f"{AI_NEWS_PROMPT}\n\nVERIFIED PAGE EVIDENCE:\n{state.get('evidence', '')}"
    return {"news": generate_response(prompt)}


def research_ai_news(state: AINewsState) -> AINewsState:
    """Search and fetch candidate news pages before generation."""
    evidence = collect_page_evidence(
        [
            "latest AI product release official announcement",
            "latest AI research robotics chips infrastructure official",
            "latest AI developer tools startup funding policy safety official",
        ],
    )
    return {"evidence": evidence}


def build_ai_news_workflow():
    """Build and compile the AI news workflow."""
    workflow = StateGraph(AINewsState)
    workflow.add_node("research_ai_news", research_ai_news)
    workflow.add_node("create_ai_news", create_ai_news)
    workflow.add_edge(START, "research_ai_news")
    workflow.add_edge("research_ai_news", "create_ai_news")
    workflow.add_edge("create_ai_news", END)
    return workflow.compile()


ai_news_workflow = build_ai_news_workflow()


def generate_ai_news() -> str:
    """Generate the daily AI news section."""
    result = ai_news_workflow.invoke({})
    return result.get("news", "")
