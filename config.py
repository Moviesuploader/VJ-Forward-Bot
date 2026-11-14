"""Application configuration loaded from environment variables."""
import os


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in your hosting provider's config vars."
        )
    return value


def _required_int(name: str) -> int:
    value = _required(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


class Config:
    API_ID = _required_int("API_ID")
    API_HASH = _required("API_HASH")
    BOT_TOKEN = _required("BOT_TOKEN")
    BOT_OWNER = _required_int("BOT_OWNER")
    DATABASE_URI = _required("DATABASE_URI")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "vj-forward-bot").strip() or "vj-forward-bot"
    BOT_SESSION = os.environ.get("BOT_SESSION", "vjbot")


class temp:
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
