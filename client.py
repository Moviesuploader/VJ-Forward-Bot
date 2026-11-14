"""Pyrogram client with a safe, local ask() conversation helper.

Pyrofork's MessageHandler contains its own listener wrapper. Using that class
for a second temporary ask handler can re-enter the same callback recursively.
This implementation uses the plain Handler base class instead.
"""
import asyncio

from pyrogram import Client, StopPropagation, filters as pyrogram_filters
from pyrogram.handlers.handler import Handler


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

        The temporary generic handler is scoped to the requested chat/user and
        is always removed, including on timeout or send failure.
        """
        response_future = asyncio.get_running_loop().create_future()

        handler_filter = pyrogram_filters.chat(chat_id)
        if user_id is not None:
            handler_filter = handler_filter & pyrogram_filters.user(user_id)
        if filters is not None:
            handler_filter = handler_filter & filters

        async def capture_response(client, message):
            if not response_future.done():
                response_future.set_result(message)
            raise StopPropagation

        # Do not use pyrogram.handlers.MessageHandler here: Pyrofork's
        # MessageHandler adds a listener wrapper of its own.
        handler = Handler(capture_response, handler_filter)
        self.add_handler(handler, group=-1)

        try:
            sent_message = await self.send_message(chat_id, text, *args, **kwargs)
            response = await asyncio.wait_for(response_future, timeout=timeout)
            response.sent_message = sent_message
            return response
        finally:
            self.remove_handler(handler, group=-1)
