import unittest

from src.tools.media_service import (
    build_caption_and_body,
    extract_media_image,
    get_category_banner,
)


class MediaServiceTests(unittest.TestCase):
    def test_category_banner_returns_valid_url(self):
        banner = get_category_banner("ai_news")
        self.assertTrue(banner.startswith("https://"))
        default_banner = get_category_banner("unknown_category")
        self.assertTrue(default_banner.startswith("https://"))

    def test_extract_media_image_finds_cloudfront_thumbnail(self):
        text = "Check out this hackathon: https://d112y698adiu2z.cloudfront.net/photos/123/thumb.png"
        extracted = extract_media_image(text)
        self.assertEqual(extracted, "https://d112y698adiu2z.cloudfront.net/photos/123/thumb.png")

    def test_extract_media_image_finds_png_url(self):
        text = "Great opportunity at https://example.com/images/banner.jpg for coders"
        extracted = extract_media_image(text)
        self.assertEqual(extracted, "https://example.com/images/banner.jpg")

    def test_extract_media_image_falls_back_to_category_banner(self):
        text = "Text without any image urls."
        extracted = extract_media_image(text, fallback_category="hackathons")
        self.assertEqual(extracted, get_category_banner("hackathons"))

    def test_build_caption_and_body_short_text(self):
        short_text = "Short telegram post"
        caption, extra_chunks = build_caption_and_body(short_text, max_caption_len=500)
        self.assertEqual(caption, short_text)
        self.assertEqual(extra_chunks, [])

    def test_build_caption_and_body_splits_long_text(self):
        long_text = "Paragraph 1\n\n" + ("Long body text " * 100)
        caption, extra_chunks = build_caption_and_body(long_text, max_caption_len=50)
        self.assertEqual(caption, "Paragraph 1")
        self.assertGreater(len(extra_chunks), 0)


if __name__ == "__main__":
    unittest.main()
