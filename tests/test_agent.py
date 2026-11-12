import unittest
from unittest.mock import patch

from src.agents.devflow_agent import assistant_node, run_agent


class AgentWorkflowTests(unittest.TestCase):
    @patch("src.agents.devflow_agent.generate_response")
    def test_assistant_node_generates_response(self, generate_response):
        generate_response.return_value = "Use a virtual environment."

        result = assistant_node({"prompt": "How do I isolate dependencies?"})

        self.assertEqual(result, {"response": "Use a virtual environment."})
        generate_response.assert_called_once_with(
            "How do I isolate dependencies?",
        )

    @patch("src.agents.devflow_agent.generate_response")
    def test_run_agent_executes_graph(self, generate_response):
        generate_response.return_value = "Graph response"

        result = run_agent("Explain LangGraph.")

        self.assertEqual(result, "Graph response")
        generate_response.assert_called_once_with("Explain LangGraph.")

    @patch("src.agents.devflow_agent.generate_response")
    def test_run_agent_returns_empty_response_when_model_returns_none(self, generate_response):
        generate_response.return_value = ""

        self.assertEqual(run_agent("Say nothing."), "")


if __name__ == "__main__":
    unittest.main()
