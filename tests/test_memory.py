import os
import tempfile
import unittest

from src.database.memory import (
    get_recently_published,
    is_url_published,
    record_opportunity,
    record_published,
)


class MemoryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_and_check_published_url(self):
        self.assertFalse(is_url_published("https://example.com/item1", self.db_path))

        success = record_published(
            title="Item 1",
            url="https://example.com/item1",
            category="news",
            content="Some story",
            channel_id="-10012345",
            db_path=self.db_path,
        )
        self.assertTrue(success)
        self.assertTrue(is_url_published("https://example.com/item1", self.db_path))

    def test_duplicate_url_ignored(self):
        record_published("Item 1", "https://example.com/item1", db_path=self.db_path)
        record_published("Item 1 duplicate", "https://example.com/item1", db_path=self.db_path)

        recent = get_recently_published(days=7, db_path=self.db_path)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["title"], "Item 1")

    def test_record_opportunity(self):
        success = record_opportunity(
            name="Kiroween 2026",
            url="https://kiroween.devpost.com/",
            deadline="2026-12-04",
            eligibility="Global",
            db_path=self.db_path,
        )
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
