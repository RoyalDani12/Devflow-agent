import unittest
from unittest.mock import patch

from src.tools.web_research import (
    MAX_EVIDENCE_CHARS,
    SearchResult,
    _unwrap_search_url,
    collect_page_evidence,
    fetch_page,
)


class WebResearchTests(unittest.TestCase):
    def test_unwraps_duckduckgo_result_url(self):
        url = (
            "https://duckduckgo.com/l/?uddg="
            "https%3A%2F%2Fexample.com%2Fofficial"
        )

        self.assertEqual(
            _unwrap_search_url(url),
            "https://example.com/official",
        )

    @patch("src.tools.web_research.urlopen")
    def test_fetch_page_converts_html_to_text(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b"<html><script>ignore()</script><p>Hello</p></html>"

        self.assertEqual(fetch_page("https://example.com/official"), "Hello")

    @patch("src.tools.web_research.fetch_page")
    @patch("src.tools.web_research.search_web")
    def test_collects_deduplicated_page_evidence(self, search_web, fetch_page):
        search_web.return_value = [
            SearchResult("Official page", "https://example.com/apply", "summary"),
            SearchResult("Duplicate", "https://example.com/apply", "summary"),
        ]
        fetch_page.return_value = "Deadline: 31 December 2099"

        evidence = collect_page_evidence(["test"], result_limit=5, page_limit=5)

        self.assertIn("SOURCE URL: https://example.com/apply", evidence)
        self.assertEqual(fetch_page.call_count, 1)

    @patch("src.tools.web_research.fetch_page")
    @patch("src.tools.web_research.search_web")
    def test_limits_combined_page_evidence(self, search_web, fetch_page):
        search_web.return_value = [
            SearchResult("Source", "https://example.com/apply", "summary"),
        ]
        fetch_page.return_value = "evidence " * MAX_EVIDENCE_CHARS

        evidence = collect_page_evidence(["test"], result_limit=1, page_limit=1)

        self.assertLessEqual(len(evidence), MAX_EVIDENCE_CHARS)


if __name__ == "__main__":
    unittest.main()
