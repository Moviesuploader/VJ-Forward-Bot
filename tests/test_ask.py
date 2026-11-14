import asyncio
import unittest
from types import SimpleNamespace

from pyrogram import StopPropagation
from pyrogram.enums import ListenerTypes
from pyrogram.handlers import MessageHandler
from pyrogram.types import Identifier

from client import VJ


class FakeBot(VJ):
    def __init__(self, reply=None, send_error=None):
        # Avoid network/client initialization; exercise the actual VJ methods.
        self.listeners = {listener_type: [] for listener_type in ListenerTypes}
        self.reply = reply
        self.send_error = send_error
        self.sent = []

    async def send_message(self, chat_id, text, *args, **kwargs):
        if self.send_error:
            raise self.send_error
        sent_message = SimpleNamespace(chat_id=chat_id, text=text)
        self.sent.append(sent_message)

        if self.reply is not None:
            async def deliver():
                await asyncio.sleep(0)
                listener = self.get_listener_matching_with_data(
                    Identifier(chat_id=chat_id, from_user_id=98765),
                    ListenerTypes.MESSAGE,
                )
                if listener and not listener.future.done():
                    listener.future.set_result(self.reply)

            asyncio.create_task(deliver())
        return sent_message


class AskHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_ask_returns_matching_message_and_cleans_listener(self):
        reply = SimpleNamespace(text="hello")
        bot = FakeBot(reply=reply)

        result = await bot.ask(
            chat_id=12345,
            text="Send a reply",
            user_id=98765,
            timeout=1,
        )

        self.assertIs(result, reply)
        self.assertEqual(result.sent_message.text, "Send a reply")
        self.assertEqual(bot.listeners[ListenerTypes.MESSAGE], [])

    async def test_ask_timeout_cleans_listener(self):
        bot = FakeBot()

        with self.assertRaises(asyncio.TimeoutError):
            await bot.ask(chat_id=12345, text="Send a reply", timeout=0.01)

        self.assertEqual(bot.listeners[ListenerTypes.MESSAGE], [])

    async def test_send_error_cleans_listener(self):
        bot = FakeBot(send_error=RuntimeError("send failed"))

        with self.assertRaisesRegex(RuntimeError, "send failed"):
            await bot.ask(chat_id=12345, text="Send a reply", timeout=1)

        self.assertEqual(bot.listeners[ListenerTypes.MESSAGE], [])

    async def test_builtin_message_handler_dispatches_without_recursion(self):
        bot = FakeBot()
        calls = []

        async def original_callback(client, message):
            calls.append(message.text)

        handler = MessageHandler(original_callback)
        message = SimpleNamespace(
            chat=SimpleNamespace(id=12345, username=None),
            from_user=SimpleNamespace(id=98765, username=None),
            id=777,
            text="normal update",
        )

        await handler.callback(bot, message)
        self.assertEqual(calls, ["normal update"])

    async def test_builtin_message_handler_resolves_ask_listener(self):
        bot = FakeBot()
        future, listener = bot._register_listener(
            chat_id=12345,
            user_id=98765,
            listener_type=ListenerTypes.MESSAGE,
        )
        handler = MessageHandler(lambda *_: None)
        message = SimpleNamespace(
            chat=SimpleNamespace(id=12345, username=None),
            from_user=SimpleNamespace(id=98765, username=None),
            id=778,
            text="answer",
        )

        with self.assertRaises(StopPropagation):
            await handler.callback(bot, message)

        self.assertEqual(future.result(), message)
        self.assertEqual(bot.listeners[ListenerTypes.MESSAGE], [])
        bot.remove_listener(listener)

    async def test_listener_matching_uses_pyrofork_listener_enum(self):
        bot = FakeBot()
        future, listener = bot._register_listener(
            chat_id=12345,
            user_id=98765,
            listener_type=ListenerTypes.MESSAGE,
        )

        found = bot.get_listener_matching_with_data(
            Identifier(chat_id=12345, from_user_id=98765),
            ListenerTypes.MESSAGE,
        )
        self.assertIs(found, listener)
        self.assertIsNone(
            bot.get_listener_matching_with_data(
                Identifier(chat_id=12345, from_user_id=11111),
                ListenerTypes.MESSAGE,
            )
        )
        bot.remove_listener(listener)
        future.cancel()


if __name__ == "__main__":
    unittest.main()
