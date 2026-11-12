from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response


class OpportunitiesState(TypedDict, total=False):
    opportunities: str


OPPORTUNITIES_PROMPT = f"""Create a Telegram-ready opportunities section for
developers. The current date is {date.today().isoformat()}. Include up to three
different hackathons, fellowships, scholarships, internships, or jobs. Do not
invent opportunities if fewer can be verified.

For every opportunity:
- Confirm it is suitable for freshers, students, or early-career applicants.
- State whether no prior professional experience is required, or explain the
  minimum experience if experience is required.
- Check whether applicants from Ethiopia are eligible.
- Include eligibility and requirements to enroll or apply.
- Include the exact deadline and timezone when available.
- Include a direct official source or application URL.
- State the deadline status as of {date.today().isoformat()}.

Verification rules:
- Check the official page for every opportunity before including it.
- Compare each deadline date and timezone with today's date.
- Exclude every past deadline, old search result, cached result, and closed
  rolling application.
- Include future-deadline opportunities only when the official page confirms
  applications are open.
- Include an Ethiopia-eligible opportunity when one is verified.
- Treat missing, unclear, or conflicting deadlines as unverified and exclude
  them unless the official source clearly confirms applications are open.
- Never invent requirements, eligibility, deadlines, URLs, or sources.

If no opportunity can be verified, say so clearly. Do not include AI news,
developer tips, interview questions, or claims that anything was published."""


def create_opportunities(state: OpportunitiesState) -> OpportunitiesState:
    """Generate a separate, reviewable opportunities section."""
    return {"opportunities": generate_response(OPPORTUNITIES_PROMPT)}


def build_opportunities_workflow():
    """Build and compile the opportunities workflow."""
    workflow = StateGraph(OpportunitiesState)
    workflow.add_node("create_opportunities", create_opportunities)
    workflow.add_edge(START, "create_opportunities")
    workflow.add_edge("create_opportunities", END)
    return workflow.compile()


opportunities_workflow = build_opportunities_workflow()


def generate_opportunities() -> str:
    """Generate the daily opportunities section."""
    result = opportunities_workflow.invoke({})
    return result.get("opportunities", "")
