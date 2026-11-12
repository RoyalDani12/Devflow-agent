import unittest
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

    def test_prompt_requires_all_content_sections(self):
        for section in (
            "AI NEWS",
            "DEVELOPER TIP",
            "INTERVIEW QUESTION",
            "OPPORTUNITY",
        ):
            self.assertIn(section, DAILY_CONTENT_PROMPT)


if __name__ == "__main__":
    unittest.main()
