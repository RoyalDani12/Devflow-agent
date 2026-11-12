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

    @patch("src.agents.devflow_agent.run_react_agent")
    def test_run_agent_routes_opportunity_requests(self, run_react_agent):
        run_react_agent.return_value = "Found opportunities"

        prompt = "for any oppent to ethiopian eligiable follewship schollars ship or hackatoon"
        result = run_agent(prompt)

        self.assertEqual(result, "Found opportunities")
        run_react_agent.assert_called_once_with(prompt)

    @patch("src.agents.devflow_agent.generate_ai_news")
    def test_run_agent_routes_news_requests(self, generate_ai_news):
        generate_ai_news.return_value = "Latest AI news"

        result = run_agent("Give me latest ai news")

        self.assertEqual(result, "Latest AI news")
        generate_ai_news.assert_called_once()


if __name__ == "__main__":
    unittest.main()
