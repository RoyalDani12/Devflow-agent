import sys
from dotenv import load_dotenv

load_dotenv(".env")

from src.agents.react_agent import build_devflow_react_agent
from src.workflows.daily_workflow import generate_daily_draft


def main():
    print("""
===================================================================
🤖 DEVFLOW AUTONOMOUS AGENT CLI
===================================================================
Commands:
  scan     - Run the autonomous daily research & verification cycle
  exit     - Exit the CLI
  <prompt> - Ask the agent anything (uses dynamic ReAct tool-calling)
===================================================================
""")
    agent = build_devflow_react_agent()

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        if user_input.lower() == "scan":
            print("\n🤖 Agent: Starting autonomous research scan across Devpost, scholarship.et, TechCrunch...")
            draft = generate_daily_draft()
            print("\n" + "=" * 60)
            print("📋 VERIFIED AUTONOMOUS DRAFT:")
            print("=" * 60)
            print(draft)
            continue

        print("\n🤖 Agent: Thinking & executing tool calls...")
        try:
            for chunk in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                stream_mode="updates",
            ):
                for node, data in chunk.items():
                    if "messages" in data:
                        for m in data["messages"]:
                            tool_calls = getattr(m, "tool_calls", None)
                            if tool_calls:
                                for tc in tool_calls:
                                    print(f"  🔧 [Tool Call] {tc['name']}({tc['args']})")
                            elif hasattr(m, "content") and m.content and node == "tools":
                                snippet = m.content[:150].replace("\n", " ")
                                print(f"  👁️  [Observation] {snippet}...")
                            elif hasattr(m, "content") and m.content and node != "tools":
                                print(f"\n🤖 Agent Response:\n{m.content}")
        except Exception as exc:
            print(f"Error running agent: {exc}")


if __name__ == "__main__":
    main()
