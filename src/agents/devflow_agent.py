from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import generate_response


class AgentState(TypedDict, total=False):
    prompt: str
    response: str


def assistant_node(state: AgentState) -> AgentState:
    """Generate an assistant response for the current prompt."""
    return {"response": generate_response(state["prompt"])}


def build_agent_graph():
    """Build and compile the initial single-node DevFlow workflow."""
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