import unittest

from src.telegram.bot import MAX_TELEGRAM_MESSAGE_LENGTH, split_message


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


if __name__ == "__main__":
    unittest.main()
