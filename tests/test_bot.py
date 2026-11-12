import os
import unittest
from unittest.mock import patch

from src.telegram.bot import (
    MAX_TELEGRAM_MESSAGE_LENGTH,
    _publish_chat_id,
    pending_drafts,
    split_message,
)


class SplitMessageTests(unittest.TestCase):
    def test_short_message_is_unchanged(self):
        self.assertEqual(split_message("hello"), ["hello"])

    def test_prefers_word_boundaries(self):
        message = "word " * (MAX_TELEGRAM_MESSAGE_LENGTH // 5 + 2)

        chunks = split_message(message)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= MAX_TELEGRAM_MESSAGE_LENGTH for chunk in chunks))
        self.assertEqual("".join(chunks).replace(" ", ""), message.replace(" ", ""))

    def test_splits_long_unbroken_text(self):
        message = "x" * (MAX_TELEGRAM_MESSAGE_LENGTH + 10)

        chunks = split_message(message)

        self.assertEqual(
            [MAX_TELEGRAM_MESSAGE_LENGTH, 10],
            [len(chunk) for chunk in chunks],
        )

    def test_never_returns_empty_chunks(self):
        message = "a" * MAX_TELEGRAM_MESSAGE_LENGTH + "\n\n"

        chunks = split_message(message)

        self.assertEqual(chunks, ["a" * MAX_TELEGRAM_MESSAGE_LENGTH])
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_whitespace_only_message_has_no_chunks(self):
        self.assertEqual(split_message(" \n\t "), [])

    def test_publish_defaults_to_review_chat(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_publish_chat_id(-100123), -100123)

    def test_publish_uses_configured_chat(self):
        with patch.dict(os.environ, {"TELEGRAM_PUBLISH_CHAT_ID": "-100456"}):
            self.assertEqual(_publish_chat_id(-100123), -100456)

    def test_publish_rejects_invalid_chat_id(self):
        with patch.dict(os.environ, {"TELEGRAM_PUBLISH_CHAT_ID": "channel"}):
            with self.assertRaises(ValueError):
                _publish_chat_id(-100123)

    def tearDown(self):
        pending_drafts.clear()


if __name__ == "__main__":
    unittest.main()
