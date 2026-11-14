"""VJ Forward Bot entry point (Heroku worker)."""
import asyncio
import logging

from pyrogram import idle

from client import VJ
from config import Config
from database import db
from plugins.regix import restart_forwards

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("vj-forward-bot")


async def main():
    await db.check_connection()
    logger.info("MongoDB connection verified")

    bot = VJ(
        "VJ-Forward-Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        plugins={"root": "plugins"},
    )

    try:
        await bot.start()
        me = await bot.get_me()
        logger.info("Telegram bot started as @%s (id=%s)", me.username, me.id)
        logger.info("Custom ask() message handler is ready")
        try:
            await restart_forwards(bot)
        except Exception:
            logger.exception("One or more pending forwarding jobs could not be resumed")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()
        await db.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
