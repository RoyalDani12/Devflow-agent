from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response
from src.agents.react_agent import run_react_agent
from src.workflows.ai_news_workflow import generate_ai_news
from src.workflows.opportunities_workflow import generate_opportunities


class AgentState(TypedDict, total=False):
    prompt: str
    response: str


OPPORTUNITY_KEYWORDS = (
    "opportunity",
    "opportunities",
    "oppent",
    "fellowship",
    "follewship",
    "scholarship",
    "scholar",
    "schollar",
    "hackathon",
    "hackatoon",
    "internship",
    "internships",
    "grant",
    "grants",
    "search deeply",
)

AI_NEWS_KEYWORDS = (
    "ai news",
    "tech news",
    "latest ai",
    "ai update",
    "ai release",
)


def assistant_node(state: AgentState) -> AgentState:
    """Generate an assistant response, routing to the autonomous ReAct agent when appropriate."""
    prompt = state.get("prompt", "")
    lower = prompt.lower()

    if any(keyword in lower for keyword in OPPORTUNITY_KEYWORDS):
        return {"response": run_react_agent(prompt)}

    if any(keyword in lower for keyword in AI_NEWS_KEYWORDS):
        return {"response": generate_ai_news()}

    return {"response": generate_response(prompt)}


def build_agent_graph():
    """Build and compile the DevFlow workflow."""
    workflow = StateGraph(AgentState)
    workflow.add_node("assistant", assistant_node)
    workflow.add_edge(START, "assistant")
    workflow.add_edge("assistant", END)
    return workflow.compile()


agent_graph = build_agent_graph()


def run_agent(prompt: str) -> str:
    """Run the DevFlow workflow and return its generated response."""
    result = agent_graph.invoke({"prompt": prompt})
    return result.get("response", "")
