import unittest
from urllib.parse import urlparse

from src.tools.sources_catalog import (
    SOURCES_CATALOG,
    get_all_sources,
    get_feed_sources,
    get_sources_by_category,
    get_total_source_count,
)


class SourcesCatalogTests(unittest.TestCase):
    def test_total_sources_exceeds_fifty(self):
        self.assertGreaterEqual(get_total_source_count(), 50)
        self.assertEqual(len(get_all_sources()), get_total_source_count())

    def test_required_categories_present(self):
        categories = {s.category for s in SOURCES_CATALOG}
        expected = {"african", "hackathon", "fellowship", "scholarship", "ai_news"}
        self.assertTrue(expected.issubset(categories))

    def test_all_sources_have_valid_metadata(self):
        for s in SOURCES_CATALOG:
            self.assertTrue(len(s.name) > 2, f"Source name too short: {s}")
            self.assertTrue(len(s.description) > 5, f"Description too short: {s}")
            parsed = urlparse(s.url)
            self.assertIn(parsed.scheme, {"http", "https"}, f"Invalid URL scheme: {s.url}")
            self.assertTrue(bool(parsed.netloc), f"Invalid netloc: {s.url}")

    def test_feed_sources_have_valid_feed_urls(self):
        feed_sources = get_feed_sources()
        self.assertGreater(len(feed_sources), 5)
        for s in feed_sources:
            self.assertIsNotNone(s.feed_url)
            parsed = urlparse(s.feed_url)
            self.assertIn(parsed.scheme, {"http", "https"})

    def test_filter_by_category(self):
        african_sources = get_sources_by_category("african")
        self.assertGreaterEqual(len(african_sources), 10)
        self.assertTrue(all(s.category == "african" for s in african_sources))


if __name__ == "__main__":
    unittest.main()
