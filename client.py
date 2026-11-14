"""Pyrogram client with a safe, local ask() conversation helper.

This deliberately avoids Pyromod's global MessageHandler monkeypatch, which
caused recursive callback dispatch with the deployed Pyrofork runtime.
"""
import asyncio

from pyrogram import Client, StopPropagation, filters
from pyrogram.handlers import MessageHandler


class VJ(Client):
    """Main bot client with an isolated one-shot message prompt helper."""

    async def ask(
        self,
        chat_id,
        text,
        filters=None,
        timeout=None,
        *args,
        user_id=None,
        **kwargs,
    ):
        """Send a prompt and await the next matching message.

        The temporary handler is scoped to the requested chat/user and is
        always removed, including on timeout or send failure.
        """
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()

        handler_filter = globals()["filters"].chat(chat_id)
        if user_id is not None:
            handler_filter = handler_filter & globals()["filters"].user(user_id)
        if filters is not None:
            handler_filter = handler_filter & filters

        async def capture_response(client, message):
            if not response_future.done():
                response_future.set_result(message)
            raise StopPropagation

        handler = MessageHandler(capture_response, handler_filter)
        self.add_handler(handler, group=-1)

        try:
            sent_message = await self.send_message(chat_id, text, *args, **kwargs)
            response = await asyncio.wait_for(response_future, timeout=timeout)
            response.sent_message = sent_message
            return response
        finally:
            self.remove_handler(handler, group=-1)
