import unittest
from unittest.mock import AsyncMock, MagicMock

from src.telegram.media_sender import publish_content_with_media, send_draft_for_review


class MediaSenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_content_sends_single_message_with_preview(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        text = "🚀 **Tech & AI Breakthroughs**\nhttps://example.com/banner.png"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertEqual(kwargs.get("chat_id"), 12345)
        self.assertIsNotNone(kwargs.get("link_preview_options"))

    async def test_publish_content_falls_back_on_preview_failure(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=[Exception("Preview error"), None])

        text = "Post without image failure recovery"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        self.assertEqual(bot.send_message.call_count, 2)

    async def test_send_draft_for_review_sends_single_message_with_keyboard(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        text = "Draft content"
        success = await send_draft_for_review(bot, 12345, text)

        self.assertTrue(success)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIsNotNone(kwargs.get("reply_markup"))


if __name__ == "__main__":
    unittest.main()
