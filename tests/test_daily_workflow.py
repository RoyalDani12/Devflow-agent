import unittest
from datetime import date
from unittest.mock import patch

from src.workflows.daily_workflow import (
    DAILY_CONTENT_PROMPT,
    create_daily_draft,
    generate_daily_draft,
)


class DailyWorkflowTests(unittest.TestCase):
    @patch("src.workflows.daily_workflow.generate_response")
    def test_create_daily_draft_generates_unpublished_package(self, generate_response):
        generate_response.return_value = "AI NEWS\n...\nOPPORTUNITY\n..."

        result = create_daily_draft({})

        self.assertEqual(result["draft"], generate_response.return_value)
        generate_response.assert_called_once_with(DAILY_CONTENT_PROMPT)

    @patch("src.workflows.daily_workflow.generate_response")
    def test_generate_daily_draft_runs_workflow(self, generate_response):
        generate_response.return_value = "Daily draft"

        self.assertEqual(generate_daily_draft(), "Daily draft")

    def test_prompt_requires_news_and_opportunity_sections(self):
        for section in ("AI NEWS", "OPPORTUNITIES"):
            self.assertIn(section, DAILY_CONTENT_PROMPT)

    def test_prompt_requires_verified_open_opportunities(self):
        current_date = date.today().isoformat()

        self.assertIn("up to three", DAILY_CONTENT_PROMPT)
        self.assertIn("up to two", DAILY_CONTENT_PROMPT)
        self.assertIn("suitable for freshers", DAILY_CONTENT_PROMPT)
        self.assertIn("no prior professional experience is required", DAILY_CONTENT_PROMPT)
        self.assertIn("Who is eligible", DAILY_CONTENT_PROMPT)
        self.assertIn("applicants from Ethiopia", DAILY_CONTENT_PROMPT)
        self.assertIn("Requirements to enroll or apply", DAILY_CONTENT_PROMPT)
        self.assertIn("direct official source", DAILY_CONTENT_PROMPT)
        self.assertIn(f"current date is {current_date}", DAILY_CONTENT_PROMPT)
        self.assertIn("compare its date and timezone", DAILY_CONTENT_PROMPT)
        self.assertIn("deadlines in the past", DAILY_CONTENT_PROMPT)
        self.assertIn("future deadlines", DAILY_CONTENT_PROMPT)
        self.assertIn("missing, unclear, or conflicting deadline", DAILY_CONTENT_PROMPT)

    def test_prompt_excludes_removed_sections(self):
        self.assertNotIn("DEVELOPER TIP", DAILY_CONTENT_PROMPT)
        self.assertNotIn("INTERVIEW QUESTION", DAILY_CONTENT_PROMPT)


if __name__ == "__main__":
    unittest.main()
