from pymongo import AsyncMongoClient
from config import Config


class Db:
    def __init__(self, uri, database_name):
        self._client = AsyncMongoClient(
            uri,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            appname="VJ-Forward-Bot",
        )
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.userbot = self.db.userbot
        self.col = self.db.users
        self.nfy = self.db.notify
        self.chl = self.db.channels

    async def check_connection(self):
        """Fail fast when MongoDB is unreachable or credentials are invalid."""
        await self._client.admin.command("ping")

    async def close(self):
        await self._client.close()

    def new_user(self, id, name):
        return {"id": id, "name": name, "ban_status": {"is_banned": False, "ban_reason": ""}}

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            await self.col.insert_one(self.new_user(id, name))

    async def is_user_exist(self, id):
        return bool(await self.col.find_one({"id": int(id)}))

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def total_users_bots_count(self):
        return await self.col.count_documents({}), await self.bot.count_documents({})

    async def remove_ban(self, id):
        await self.col.update_one({"id": int(id)}, {"$set": {"ban_status": {"is_banned": False, "ban_reason": ""}}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        await self.col.update_one({"id": int(user_id)}, {"$set": {"ban_status": {"is_banned": True, "ban_reason": ban_reason}}})

    async def get_ban_status(self, id):
        default = {"is_banned": False, "ban_reason": ""}
        user = await self.col.find_one({"id": int(id)})
        return user.get("ban_status", default) if user else default

    def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    async def get_banned(self):
        users = self.col.find({"ban_status.is_banned": True})
        return [user["id"] async for user in users]

    async def update_configs(self, id, configs):
        await self.col.update_one({"id": int(id)}, {"$set": {"configs": configs}}, upsert=True)

    async def get_configs(self, id):
        default = {
            "caption": None, "duplicate": True, "forward_tag": False,
            "min_size": 0, "max_size": 0, "extension": None,
            "keywords": None, "protect": None, "button": None, "db_uri": None,
            "filters": {"poll": True, "text": True, "audio": True, "voice": True,
                        "video": True, "photo": True, "document": True,
                        "animation": True, "sticker": True},
        }
        user = await self.col.find_one({"id": int(id)})
        if not user:
            return default
        configs = user.get("configs", {})
        merged = {**default, **configs}
        merged["filters"] = {**default["filters"], **configs.get("filters", {})}
        return merged

    async def add_bot(self, datas):
        if not await self.is_bot_exist(datas["user_id"]):
            await self.bot.insert_one(datas)

    async def remove_bot(self, user_id):
        await self.bot.delete_many({"user_id": int(user_id)})

    async def get_bot(self, user_id: int):
        return await self.bot.find_one({"user_id": int(user_id)})

    async def is_bot_exist(self, user_id):
        return bool(await self.get_bot(user_id))

    async def add_userbot(self, datas):
        if not await self.is_userbot_exist(datas["user_id"]):
            await self.userbot.insert_one(datas)

    async def remove_userbot(self, user_id):
        await self.userbot.delete_many({"user_id": int(user_id)})

    async def get_userbot(self, user_id: int):
        return await self.userbot.find_one({"user_id": int(user_id)})

    async def is_userbot_exist(self, user_id):
        return bool(await self.get_userbot(user_id))

    async def in_channel(self, user_id: int, chat_id: int) -> bool:
        return bool(await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)}))

    async def add_channel(self, user_id: int, chat_id: int, title, username):
        if await self.in_channel(user_id, chat_id):
            return False
        return await self.chl.insert_one({"user_id": int(user_id), "chat_id": int(chat_id), "title": title, "username": username})

    async def remove_channel(self, user_id: int, chat_id: int):
        if not await self.in_channel(user_id, chat_id):
            return False
        return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_channel_details(self, user_id: int, chat_id: int):
        return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_user_channels(self, user_id: int):
        return [channel async for channel in self.chl.find({"user_id": int(user_id)})]

    async def get_filters(self, user_id):
        configs = await self.get_configs(user_id)
        return [str(key) for key, enabled in configs["filters"].items() if enabled is False]

    async def add_frwd(self, user_id):
        return await self.nfy.update_one({"user_id": int(user_id)}, {"$setOnInsert": {"user_id": int(user_id)}}, upsert=True)

    async def rmve_frwd(self, user_id=0, all=False):
        return await self.nfy.delete_many({} if all else {"user_id": int(user_id)})

    def get_all_frwd(self):
        return self.nfy.find({})

    async def forwad_count(self):
        return await self.nfy.count_documents({})

    async def is_forwad_exit(self, user):
        return bool(await self.nfy.find_one({"user_id": int(user)}))

    async def get_forward_details(self, user_id):
        default = {"chat_id": None, "forward_id": None, "toid": None, "last_id": None,
                   "limit": None, "msg_id": None, "start_time": None, "fetched": 0,
                   "offset": 0, "deleted": 0, "total": 0, "duplicate": 0,
                   "skip": 0, "filtered": 0}
        user = await self.nfy.find_one({"user_id": int(user_id)})
        return {**default, **(user.get("details", {}) if user else {})}

    async def update_forward(self, user_id, details):
        await self.nfy.update_one({"user_id": int(user_id)}, {"$set": {"details": details}}, upsert=True)


db = Db(Config.DATABASE_URI, Config.DATABASE_NAME)
