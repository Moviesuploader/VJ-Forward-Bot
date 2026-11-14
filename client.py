"""Pyrofork client with a native listener/ask implementation.

Pyrofork already wraps MessageHandler with listener dispatch. Importing the
separate Pyromod package patches that same handler a second time and causes
recursive callback execution. This class implements the small listener API
expected by Pyrofork directly, without monkeypatching its handlers.
"""
import asyncio
from typing import Optional

from pyrogram import Client
from pyrogram.enums import ListenerTypes
from pyrogram.types import Identifier, Listener


class VJ(Client):
    """Main bot client with Pyrofork-compatible ask/listen helpers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use Pyrofork's own enum class. A different ListenerTypes enum creates
        # keys that Pyrofork's built-in MessageHandler cannot find.
        self.listeners = {listener_type: [] for listener_type in ListenerTypes}

    def _register_listener(
        self,
        *,
        filters=None,
        listener_type=ListenerTypes.MESSAGE,
        unallowed_click_alert=True,
        chat_id=None,
        user_id=None,
        message_id=None,
        inline_message_id=None,
    ):
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        future = asyncio.get_running_loop().create_future()
        listener = Listener(
            future=future,
            filters=filters,
            unallowed_click_alert=unallowed_click_alert,
            identifier=pattern,
            listener_type=listener_type,
        )
        self.listeners[listener_type].append(listener)
        future.add_done_callback(lambda _future: self.remove_listener(listener))
        return future, listener

    def remove_listener(self, listener):
        try:
            self.listeners[listener.listener_type].remove(listener)
        except (KeyError, ValueError):
            pass

    def get_listener_matching_with_data(self, data, listener_type):
        matching = [
            listener
            for listener in self.listeners[listener_type]
            if listener.identifier.matches(data)
        ]
        return max(
            matching,
            key=lambda item: item.identifier.count_populated(),
            default=None,
        )

    async def listen(
        self,
        filters=None,
        listener_type=ListenerTypes.MESSAGE,
        timeout=None,
        unallowed_click_alert=True,
        chat_id=None,
        user_id=None,
        message_id=None,
        inline_message_id=None,
    ):
        future, listener = self._register_listener(
            filters=filters,
            listener_type=listener_type,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self.remove_listener(listener)

    async def ask(
        self,
        chat_id,
        text,
        filters=None,
        listener_type=ListenerTypes.MESSAGE,
        timeout=None,
        unallowed_click_alert=True,
        user_id=None,
        message_id=None,
        inline_message_id=None,
        *args,
        **kwargs,
    ):
        """Send a prompt and await a matching response without monkeypatches."""
        future, listener = self._register_listener(
            filters=filters,
            listener_type=listener_type,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        try:
            sent_message = None
            if text and text.strip():
                sent_message = await self.send_message(
                    chat_id, text, *args, **kwargs
                )
            response = await asyncio.wait_for(future, timeout=timeout)
            response.sent_message = sent_message
            return response
        finally:
            self.remove_listener(listener)
