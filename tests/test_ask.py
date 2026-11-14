import asyncio
import unittest
from types import SimpleNamespace

from pyrogram import StopPropagation, filters
from pyrogram.handlers import MessageHandler

from client import VJ


class FakeBot:
    def __init__(self, reply=None, send_error=None):
        self.reply = reply
        self.send_error = send_error
        self.handler = None
        self.added = []
        self.removed = []

    def add_handler(self, handler, group=0):
        self.handler = handler
        self.added.append((handler, group))

    def remove_handler(self, handler, group=0):
        self.removed.append((handler, group))
        if self.handler is handler:
            self.handler = None

    async def send_message(self, chat_id, text, *args, **kwargs):
        if self.send_error:
            raise self.send_error
        if self.reply is not None:
            try:
                await self.handler.callback(self, self.reply)
            except StopPropagation:
                pass
        return SimpleNamespace(chat_id=chat_id, text=text)


class AskHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_ask_returns_matching_message_and_cleans_handler(self):
        reply = SimpleNamespace(text="hello")
        bot = FakeBot(reply=reply)

        result = await VJ.ask(
            bot,
            chat_id=12345,
            text="Send a reply",
            filters=filters.text,
            timeout=1,
        )

        self.assertIs(result, reply)
        self.assertEqual(result.sent_message.text, "Send a reply")
        self.assertEqual(len(bot.added), 1)
        self.assertEqual(bot.added[0][1], -1)
        self.assertEqual(bot.removed, bot.added)
        self.assertIsNone(bot.handler)

    async def test_ask_timeout_cleans_handler(self):
        bot = FakeBot()

        with self.assertRaises(asyncio.TimeoutError):
            await VJ.ask(bot, chat_id=12345, text="Send a reply", timeout=0.01)

        self.assertEqual(bot.removed, bot.added)
        self.assertIsNone(bot.handler)

    async def test_send_error_cleans_handler(self):
        error = RuntimeError("send failed")
        bot = FakeBot(send_error=error)

        with self.assertRaisesRegex(RuntimeError, "send failed"):
            await VJ.ask(bot, chat_id=12345, text="Send a reply", timeout=1)

        self.assertEqual(bot.removed, bot.added)
        self.assertIsNone(bot.handler)


if __name__ == "__main__":
    unittest.main()
