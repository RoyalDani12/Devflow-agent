from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response
from src.tools.media_service import strip_markdown_asterisks
from src.tools.web_research import collect_page_evidence


class OpportunitiesState(TypedDict, total=False):
    query: str
    evidence: str
    opportunities: str


OPPORTUNITIES_PROMPT = f"""You are DevFlow's opportunity research scout. Current date: {date.today().isoformat()}.
Present verified developer opportunities (up to three or more high-impact hackathons, fellowships, scholarships, grants, internships).

CRITICAL FORMATTING & STYLE RULES:
- Never output meta text like 'Telegram-ready...', 'Here are opportunities...', or prompt instructions.
- Separate each distinct opportunity with: ===ITEM===
- Format each opportunity with an authoritative journal-style heading and clean bullet points (•):

===ITEM===
🎓 GLOBAL OPPORTUNITY DISPATCH | ETHIOPIA ELIGIBLE
🌟 Program: [Program or Hackathon Name]

• Host Organization: [Organization / Platform]
• Eligibility: [Suitable for students, freshers, or early-career applicants; state whether applicants from Ethiopia are eligible]
• Funding & Awards: [Fully Funded / Cash Prize / Stipend / Free]
• Deadline Status: [Month Day, Year - Status as of today]
• Application Portal: [Direct Application URL]
• Program Overview: [1-2 sentences on what developers gain]

Verification Rules:
- Search globally: the opportunity may be hosted anywhere in the world.
- Compare each deadline date and timezone with today's date ({date.today().isoformat()}).
- Exclude every past deadline, expired opportunity, and closed rolling call.
- Include future-deadline opportunities only when confirmed open.
- Never invent deadlines, requirements, or links.
- Absolutely NO markdown tables (|---|---|), ASCII table borders, or asterisks (* or **).
- ZERO ASTERISKS: Do NOT use bold asterisks (* or **) anywhere in the response. Use clean plain text and emojis only.
- You do NOT have a web browser or tools. Do not emit tool calls like browser.open or browser.search.
If evidence is insufficient, state: "🎯 No verified active opportunities found today."
"""


def create_opportunities(state: OpportunitiesState) -> OpportunitiesState:
    """Generate a separate, reviewable opportunities section without asterisks."""
    prompt = f"{OPPORTUNITIES_PROMPT}\n\nVERIFIED PAGE EVIDENCE:\n{state.get('evidence', '')}"
    return {"opportunities": strip_markdown_asterisks(generate_response(prompt))}


def research_opportunities(state: OpportunitiesState) -> OpportunitiesState:
    """Search and fetch candidate opportunity pages before generation."""
    user_query = state.get("query", "")
    queries = [
        "scholarships fellowships Ethiopian students open applications",
        "global hackathon devpost open Ethiopian eligible",
        "international internship fellowship scholarship open applications",
        "entry-level technology opportunities open applications worldwide",
    ]
    if user_query:
        queries.insert(0, user_query)
    evidence = collect_page_evidence(queries)
    return {"evidence": evidence}


def build_opportunities_workflow():
    """Build and compile the opportunities workflow."""
    workflow = StateGraph(OpportunitiesState)
    workflow.add_node("research_opportunities", research_opportunities)
    workflow.add_node("create_opportunities", create_opportunities)
    workflow.add_edge(START, "research_opportunities")
    workflow.add_edge("research_opportunities", "create_opportunities")
    workflow.add_edge("create_opportunities", END)
    return workflow.compile()


opportunities_workflow = build_opportunities_workflow()


def generate_opportunities(query: str | None = None) -> str:
    """Generate the daily opportunities section."""
    payload = {"query": query} if query else {}
    result = opportunities_workflow.invoke(payload)
    return result.get("opportunities", "")
