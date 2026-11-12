from datetime import date
import unittest
from unittest.mock import patch

from src.tools.agent_tools import (
    check_channel_memory_tool,
    fetch_page_content_tool,
    get_current_date,
    save_opportunity_to_memory_tool,
    search_web_tool,
)
from src.tools.web_research import SearchResult


class AgentToolsTests(unittest.TestCase):
    def test_get_current_date_returns_iso_date(self):
        self.assertEqual(get_current_date.invoke({}), date.today().isoformat())

    @patch("src.tools.agent_tools.search_web")
    def test_search_web_tool_formats_results(self, mock_search):
        mock_search.return_value = [
            SearchResult("Kiroween 2026", "https://kiroween.devpost.com/", "Online hackathon"),
        ]
        result = search_web_tool.invoke({"query": "hackathons"})
        self.assertIn("Kiroween 2026", result)
        self.assertIn("https://kiroween.devpost.com/", result)

    @patch("src.tools.agent_tools.fetch_page")
    def test_fetch_page_content_tool(self, mock_fetch):
        mock_fetch.return_value = "Opportunity deadline is Dec 2026"
        result = fetch_page_content_tool.invoke({"url": "https://example.com"})
        self.assertEqual(result, "Opportunity deadline is Dec 2026")

    @patch("src.tools.agent_tools.get_recently_published")
    def test_check_channel_memory_tool(self, mock_get_recent):
        mock_get_recent.return_value = [
            {"category": "opportunity", "title": "Old Grant", "url": "https://old.com", "published_at": "2026-11-01"},
        ]
        result = check_channel_memory_tool.invoke({"days": 30})
        self.assertIn("Old Grant", result)
        self.assertIn("https://old.com", result)

    @patch("src.tools.agent_tools.record_opportunity")
    def test_save_opportunity_tool(self, mock_record):
        result = save_opportunity_to_memory_tool.invoke({
            "name": "New Fellow",
            "url": "https://new.com",
            "deadline": "2026-12-01",
            "eligibility": "Global",
        })
        self.assertIn("Saved opportunity", result)
        mock_record.assert_called_once()


if __name__ == "__main__":
    unittest.main()
