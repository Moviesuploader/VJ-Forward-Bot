import os
import unittest

os.environ.setdefault("API_ID", "123456")
os.environ.setdefault("API_HASH", "test_api_hash")
os.environ.setdefault("BOT_TOKEN", "123456789:abcdefghijklmnopqrstuvwxyzABCDEFG")
os.environ.setdefault("BOT_OWNER", "123456")
os.environ.setdefault("DATABASE_URI", "mongodb://127.0.0.1:27017/test")

from plugins.regix import size_filter, keyword_filter, extension_filter, TimeFormatter


class ForwardFilterTests(unittest.IsolatedAsyncioTestCase):
    async def test_size_filter_min_only(self):
        self.assertTrue(await size_filter(0, 10, 5 * 1024 * 1024))
        self.assertFalse(await size_filter(0, 10, 15 * 1024 * 1024))

    async def test_size_filter_max_only(self):
        self.assertFalse(await size_filter(10, 0, 5 * 1024 * 1024))
        self.assertTrue(await size_filter(10, 0, 15 * 1024 * 1024))

    async def test_size_filter_range_inclusive(self):
        self.assertTrue(await size_filter(10, 5, 4 * 1024 * 1024))
        self.assertFalse(await size_filter(10, 5, 5 * 1024 * 1024))
        self.assertFalse(await size_filter(10, 5, 10 * 1024 * 1024))
        self.assertTrue(await size_filter(10, 5, 11 * 1024 * 1024))

    async def test_keyword_filter_keeps_matching_names(self):
        self.assertFalse(await keyword_filter("1080p|WEB-DL", "Movie.1080p.mkv"))
        self.assertTrue(await keyword_filter(["1080p", "WEB-DL"], "Movie.720p.mkv"))
        self.assertFalse(await keyword_filter(None, "Movie.mkv"))

    async def test_extension_filter_skips_matching_extensions(self):
        self.assertTrue(await extension_filter([r"\.mkv$", r"\.mp4$"], "Movie.mkv"))
        self.assertFalse(await extension_filter([r"\.mkv$"], "Movie.avi"))
        self.assertFalse(await extension_filter(None, "Movie.mkv"))

    def test_time_formatter(self):
        self.assertEqual(TimeFormatter(61000), "1m, 1s")


if __name__ == "__main__":
    unittest.main()
