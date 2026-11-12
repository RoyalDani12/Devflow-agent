import unittest
from unittest.mock import patch

from src.workflows.daily_workflow import create_daily_content, generate_daily_draft


class DailyWorkflowTests(unittest.TestCase):
    @patch("src.workflows.daily_workflow.generate_opportunities")
    @patch("src.workflows.daily_workflow.generate_ai_news")
    def test_daily_workflow_combines_independent_outputs(
        self,
        generate_ai_news,
        generate_opportunities,
    ):
        generate_ai_news.return_value = "AI NEWS"
        generate_opportunities.return_value = "OPPORTUNITIES"

        result = create_daily_content({})

        self.assertEqual(result["news"], "AI NEWS")
        self.assertEqual(result["opportunities"], "OPPORTUNITIES")
        self.assertEqual(result["draft"], "AI NEWS\n\nOPPORTUNITIES")

    @patch("src.workflows.daily_workflow.daily_workflow.invoke")
    def test_generate_daily_draft_returns_combined_draft(self, invoke):
        invoke.return_value = {"draft": "Combined draft"}

        self.assertEqual(generate_daily_draft(), "Combined draft")
        invoke.assert_called_once_with({})


if __name__ == "__main__":
    unittest.main()
