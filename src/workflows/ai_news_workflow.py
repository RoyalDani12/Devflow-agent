from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response
from src.tools.web_research import collect_page_evidence


class AINewsState(TypedDict, total=False):
    evidence: str
    news: str


AI_NEWS_PROMPT = f"""You are DevFlow's autonomous tech editor. Current date: {date.today().isoformat()}.
Generate a high-impact AI and developer tech news briefing based ONLY on the verified evidence below.
Include no more than two recent, high-impact items. Do not limit coverage to AI models.

CRITICAL FORMATTING & STYLE RULES:
- Never output meta text like 'Telegram-ready...', 'Here is the draft...', or prompt instructions.
- Start directly with:
🚀 **Tech & AI Breakthroughs**
- Absolutely NO markdown tables (|---|---|), ASCII table borders, or multiple consecutive asterisks (***).
- Format each item as a sleek Telegram card using clean emoji bullets:

⚡ **[Direct Headline of What Changed or Launched]**
🏷️ **Category:** [Model / Infrastructure / Developer Tool / Robotics / Research]
📅 **Date:** [Publication Date]
💡 **Why developers should care:** [Explain what is genuinely new or different and why developers should care]
🔗 **Read Source:** [Include a direct source URL]

- Never invent a story, date, or source.
- You do NOT have a web browser or tools. Do not emit tool calls like browser.open or browser.search.
If evidence is insufficient, state: "⚡ No verified breaking AI updates today."
"""


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
