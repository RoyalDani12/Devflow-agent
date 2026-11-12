import unittest
from datetime import date
from unittest.mock import patch

from src.workflows.ai_news_workflow import (
    AI_NEWS_PROMPT,
    create_ai_news,
    generate_ai_news,
)
from src.workflows.opportunities_workflow import (
    OPPORTUNITIES_PROMPT,
    create_opportunities,
    generate_opportunities,
)


class ContentWorkflowTests(unittest.TestCase):
    @patch("src.workflows.ai_news_workflow.generate_response")
    def test_ai_news_workflow_returns_news(self, generate_response):
        generate_response.return_value = "Two verified stories"

        self.assertEqual(create_ai_news({})["news"], "Two verified stories")
        prompt = generate_response.call_args.args[0]
        self.assertIn(AI_NEWS_PROMPT, prompt)
        self.assertIn("VERIFIED PAGE EVIDENCE:", prompt)

    @patch("src.workflows.opportunities_workflow.generate_response")
    def test_opportunities_workflow_returns_opportunities(self, generate_response):
        generate_response.return_value = "Verified opportunities"

        self.assertEqual(
            create_opportunities({})["opportunities"],
            "Verified opportunities",
        )
        prompt = generate_response.call_args.args[0]
        self.assertIn(OPPORTUNITIES_PROMPT, prompt)
        self.assertIn("VERIFIED PAGE EVIDENCE:", prompt)

    def test_news_prompt_has_separate_limits_and_sources(self):
        self.assertIn("no more than two", AI_NEWS_PROMPT)
        self.assertIn("direct source URL", AI_NEWS_PROMPT)
        self.assertIn("Do not limit coverage to AI models", AI_NEWS_PROMPT)
        self.assertIn("what is genuinely new or different", AI_NEWS_PROMPT)
        self.assertIn("why developers should care", AI_NEWS_PROMPT)
        self.assertIn(date.today().isoformat(), AI_NEWS_PROMPT)
        self.assertNotIn("OPPORTUNIT", AI_NEWS_PROMPT)

    def test_opportunities_prompt_has_verification_rules(self):
        self.assertIn("up to three", OPPORTUNITIES_PROMPT)
        self.assertIn("freshers", OPPORTUNITIES_PROMPT)
        self.assertIn("applicants from Ethiopia", OPPORTUNITIES_PROMPT)
        self.assertIn("Search globally", OPPORTUNITIES_PROMPT)
        self.assertIn("may be hosted anywhere in the world", OPPORTUNITIES_PROMPT)
        self.assertIn("Compare each deadline date and timezone", OPPORTUNITIES_PROMPT)
        self.assertIn("Exclude every past deadline", OPPORTUNITIES_PROMPT)
        self.assertNotIn("AI NEWS -", OPPORTUNITIES_PROMPT)


if __name__ == "__main__":
    unittest.main()
