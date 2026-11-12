import os
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.config import get_required_setting
from src.tools.agent_tools import ALL_AGENT_TOOLS

AGENT_SYSTEM_PROMPT = """You are DevFlow Agent, an autonomous developer community manager and research assistant.
Your goal is to discover, verify, and present high-impact tech opportunities (fellowships, hackathons, scholarships, grants) and breaking AI news for developers.

Core Operating Principles:
1. Temporal Awareness: Always check `get_current_date` to know today's date. Compare deadlines to today and NEVER recommend past or expired deadlines.
2. Avoid Repetition: Use `check_channel_memory_tool` to see what has already been published recently so you do not repeat duplicate opportunities or stories.
3. Deep Research & Verification: When candidate opportunities appear, call `fetch_page_content_tool` to inspect page content for eligibility and deadlines. If a page is protected or fails to fetch, do NOT retry or attempt proxy URLs; use the verified search snippet information directly.
4. Absolute Grounding: Never hallucinate requirements, organizations, links, or dates. Rely strictly on data observed from tools.
5. Telegram-Ready Output: Deliver clean, structured markdown tables summarizing Opportunity Name, Eligibility, Deadline, Application instructions, and Direct Source Link.
"""


def get_agent_llm(model: str = "openai/gpt-oss-20b") -> ChatOpenAI:
    """Instantiate the Groq LLM client via ChatOpenAI."""
    api_key = os.getenv("GROQ_API_KEY") or get_required_setting("GROQ_API_KEY")
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://api.groq.com/openai/v1",
        max_tokens=4096,
        temperature=0.3,
    )


def build_devflow_react_agent(llm=None, tools=None):
    """Build and compile the autonomous ReAct agent."""
    agent_llm = llm or get_agent_llm()
    agent_tools = tools or ALL_AGENT_TOOLS
    return create_agent(
        agent_llm,
        agent_tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
    )


_react_agent_instance = None


def get_react_agent():
    """Singleton getter for the compiled ReAct agent."""
    global _react_agent_instance
    if _react_agent_instance is None:
        _react_agent_instance = build_devflow_react_agent()
    return _react_agent_instance


def run_react_agent(user_prompt: str) -> str:
    """Run the autonomous ReAct agent for a given goal or user query."""
    agent = get_react_agent()
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_prompt}],
    })
    messages = result.get("messages", [])
    if messages:
        return messages[-1].content or ""
    return ""
