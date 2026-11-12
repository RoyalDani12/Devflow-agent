from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response


class DailyContentState(TypedDict, total=False):
    draft: str


DAILY_CONTENT_PROMPT = """Create a daily Telegram channel content package for
developers. Return exactly four clearly labelled sections:

1. AI NEWS - one recent AI or technology story. Include its source.
2. DEVELOPER TIP - one practical programming or software engineering tip.
3. INTERVIEW QUESTION - one technical interview question with a concise answer.
4. OPPORTUNITY - one hackathon, fellowship, scholarship, internship, or job.
   Include the deadline and official source when known. If you cannot verify
   an opportunity, say so instead of inventing details.

Use concise, Telegram-ready formatting. Do not claim to have published
anything. This is a draft for human review."""


def create_daily_draft(state: DailyContentState) -> DailyContentState:
    """Generate one reviewable content package without publishing it."""
    return {"draft": generate_response(DAILY_CONTENT_PROMPT)}


def build_daily_workflow():
    """Build and compile the daily draft workflow."""
    workflow = StateGraph(DailyContentState)
    workflow.add_node("create_daily_draft", create_daily_draft)
    workflow.add_edge(START, "create_daily_draft")
    workflow.add_edge("create_daily_draft", END)
    return workflow.compile()


daily_workflow = build_daily_workflow()


def generate_daily_draft() -> str:
    """Generate a daily channel draft for review."""
    result = daily_workflow.invoke({})
    return result.get("draft", "")