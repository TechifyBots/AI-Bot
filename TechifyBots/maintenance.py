from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMIN, DB_URI, DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB setup
mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]
settings_col = db["settings"]

# --- DB Helpers ---
async def get_maintenance() -> bool:
    data = await settings_col.find_one({"_id": "maintenance"})
    return data.get("status", False) if data else False

async def set_maintenance(status: bool):
    await settings_col.update_one(
        {"_id": "maintenance"},
        {"$set": {"status": status}},
        upsert=True
    )

# --- Command ---
@Client.on_message(filters.command("maintenance") & filters.user(ADMIN))
async def maintenance_cmd(_, m: Message):
    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        return await m.reply("Usage: /maintenance [on/off]")
    status = args[1].lower()
    if status == "on":
        if await get_maintenance():
            return await m.reply("⚠️ Maintenance mode is already enabled.")
        await set_maintenance(True)
        return await m.reply("✅ Maintenance mode **enabled**.")
    elif status == "off":
        if not await get_maintenance():
            return await m.reply("⚠️ Maintenance mode is already disabled.")
        await set_maintenance(False)
        return await m.reply("❌ Maintenance mode **disabled**.")
    else:
        await m.reply("Invalid status. Use 'on' or 'off'.")
