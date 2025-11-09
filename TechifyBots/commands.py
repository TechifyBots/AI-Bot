from pyrogram import Client, filters
from pyrogram.types import *
import requests
import random
from config import *
import google.generativeai as genai
import asyncio
from .db import tb
from .fsub import get_fsub
from Script import text
from .maintenance import get_maintenance

genai.configure(api_key=GOOGLE_API_KEY)

responses_dict = {}

@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    if await tb.get_user(message.from_user.id) is None:
        await tb.add_user(message.from_user.id, message.from_user.first_name)
        bot = await client.get_me()
        await client.send_message(
            LOG_CHANNEL,
            text.LOG.format(
                message.from_user.id,
                getattr(message.from_user, "dc_id", "N/A"),
                message.from_user.first_name or "N/A",
                f"@{message.from_user.username}" if message.from_user.username else "N/A",
                bot.username
            )
        )
    if IS_FSUB and not await get_fsub(client, message):return
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=text.START.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ℹ️ 𝖠𝖻𝗈𝗎𝗍", callback_data="about"),
             InlineKeyboardButton("📚 𝖧𝖾𝗅𝗉", callback_data="help")],
            [InlineKeyboardButton("👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋 👨‍💻", user_id=int(ADMIN))]
        ])
    )

@Client.on_message(filters.private & filters.command("ask"))
async def askcmd(client, message):
    await message.reply_text(text="**You don't need to use this command here. Ask me directly.\n\nEx:** `Who Is Lord Shiva?`\n**Ok ?? Let's Try 😏**")

@Client.on_message(filters.command("ask") & filters.group)
async def group_ai_reply(client, message):
    if len(message.command) == 1:
        return await message.reply_text(
            "⚠️ **Please provide a query after the command.**\n\nExample: `/ask What is AI?`",
            quote=True
        )
    await handle_gemini_mode(client, message)

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "ask"]))
async def handle_ai_query(client, message):
    if IS_FSUB and not await get_fsub(client, message):return
    await handle_gemini_mode(client, message)

async def handle_gemini_mode(client, message):
    if await get_maintenance() and message.from_user.id != ADMIN:
        await message.delete()
        return await message.reply_text(f"<b>{message.from_user.mention},\n\nᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ.\n\n<blockquote>ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ ꜰᴏʀ ᴍᴏʀᴇ ɪɴꜰᴏ.</blockquote></b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 ᴏᴡɴᴇʀ 👨‍💻", user_id=int(ADMIN))]]))
    user_input = message.text.strip()
    s = await message.reply_sticker("CAACAgQAAxkBAAIFqGc04PwJshM42NKq2lOFn-q5lQtqAAJuDwAC4eqxUNoxB5joJxGiHgQ")
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-lite",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    try:
        prompt_parts = [user_input]
        response = model.generate_content(prompt_parts)
        if hasattr(response, 'text') and response.text:
            await client.send_message(
                LOG_CHANNEL,
                text=f"👤 {message.from_user.mention} (`{message.from_user.id}`)\n\n"
                     f"**Query:** `{user_input}`\n\n**AI Generated Response (Gemini):**\n{response.text}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Close", callback_data="close")]]
                )
            )
            ai_message = await message.reply_text(
                f"**{message.from_user.mention},** {response.text}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ʟᴇᴀʀɴ ᴄᴏᴅɪɴɢ 👨‍💻", url="https://techifybots.blogspot.com")]]
                )
            )
            await s.delete()
            await asyncio.sleep(300)
            await message.delete()
            await ai_message.delete()
        else:
            await message.reply_text("⚠️ The AI model couldn't generate a response. Please try again.")
    except Exception as e:
        await message.reply_text("⚠️ An error occurred while processing your query. Please try again.")
        print(f"Error in Gemini Mode: {e}")
