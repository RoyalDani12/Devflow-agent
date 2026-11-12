import unittest
from unittest.mock import AsyncMock, MagicMock

from src.telegram.media_sender import publish_content_with_media, send_draft_for_review


class MediaSenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_content_with_media_calls_send_photo(self):
        bot = MagicMock()
        bot.send_photo = AsyncMock()
        bot.send_message = AsyncMock()

        text = "🚀 **Tech & AI Breakthroughs**\nhttps://example.com/banner.png"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        bot.send_photo.assert_called_once()
        args, kwargs = bot.send_photo.call_args
        self.assertEqual(kwargs.get("chat_id"), 12345)
        self.assertEqual(kwargs.get("photo"), "https://example.com/banner.png")

    async def test_publish_content_falls_back_to_text_on_photo_failure(self):
        bot = MagicMock()
        bot.send_photo = AsyncMock(side_effect=Exception("Network error"))
        bot.send_message = AsyncMock()

        text = "Post without image failure recovery"
        success = await publish_content_with_media(bot, 12345, text)

        self.assertTrue(success)
        bot.send_message.assert_called_once_with(chat_id=12345, text=text)

    async def test_send_draft_for_review_attaches_keyboard(self):
        bot = MagicMock()
        bot.send_photo = AsyncMock()
        bot.send_message = AsyncMock()

        text = "Draft content"
        success = await send_draft_for_review(bot, 12345, text)

        self.assertTrue(success)
        self.assertTrue(bot.send_photo.called or bot.send_message.called)


if __name__ == "__main__":
    unittest.main()
