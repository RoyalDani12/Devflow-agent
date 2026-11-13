import unittest
from unittest.mock import AsyncMock, MagicMock

from src.telegram.media_sender import publish_content_with_media, send_draft_for_review


class MediaSenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_content_sends_separate_messages_for_sections(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        text = "🚀 Tech & AI Breakthroughs\nhttps://example.com/ai.png\n\n===SECTION===\n\n🎯 Top Opportunities\nhttps://example.com/opp.png"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        self.assertEqual(bot.send_message.call_count, 2)

    async def test_publish_content_falls_back_on_preview_failure(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=[Exception("Preview error"), None])

        text = "Post without image failure recovery"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        self.assertEqual(bot.send_message.call_count, 2)

    async def test_send_draft_delivers_separate_messages_and_attaches_keyboard(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        sections = ["🚀 Tech & AI Breakthroughs", "🎯 Top Opportunities"]
        success = await send_draft_for_review(bot, 12345, sections)

        self.assertTrue(success)
        self.assertEqual(bot.send_message.call_count, 2)
        # Verify the reply markup is attached to the final section
        last_call_kwargs = bot.send_message.call_args_list[-1].kwargs
        self.assertIsNotNone(last_call_kwargs.get("reply_markup"))


if __name__ == "__main__":
    unittest.main()
