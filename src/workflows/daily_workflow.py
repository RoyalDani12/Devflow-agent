from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response


class DailyContentState(TypedDict, total=False):
    draft: str


DAILY_CONTENT_PROMPT = f"""Create a daily Telegram channel content package for
developers. The current date is {date.today().isoformat()}. Return exactly two
clearly labelled sections:

1. AI NEWS - up to two recent AI or technology stories. Include the source
  for each story. If no story can be verified, say so.
2. OPPORTUNITIES - include up to three different hackathons, fellowships,
  scholarships, internships, or jobs. Do not invent opportunities if fewer
  than three can be verified.

For every opportunity, include:
- Name and type.
- Confirm it is suitable for freshers, students, or early-career applicants.
- State clearly that no prior professional experience is required, or explain
 the minimum experience if experience is required.
- Who is eligible, including whether applicants from Ethiopia are eligible.
- Requirements to enroll or apply.
- Exact deadline with timezone when available.
- A direct official source or application URL.
- Deadline status as of {date.today().isoformat()}.

Opportunity verification rules:
- Use current, real information from official sources, not memory.
- Check the official page for each opportunity before including it.
- Read the deadline from the official page and compare its date and timezone
 with today's date ({date.today().isoformat()}).
- Exclude opportunities with deadlines in the past, even if they appear in
 old search results or cached pages.
- Include opportunities with future deadlines only when the official page
 confirms applications are open.
- Include at least one opportunity open to applicants from Ethiopia when a
 verified opportunity is available. If none can be verified, say so clearly.
- Treat a missing, unclear, or conflicting deadline as unverified and exclude
 it unless the official source clearly confirms that applications are open.
- Never invent a deadline, requirement, eligibility rule, URL, or source.

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