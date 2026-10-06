import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp
from config import Config

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SSVibeMusicBot")

# Client Setup
app = Client(
    "SSVibeMusicBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


call_py = PyTgCalls(app)

# Helper to fetch YouTube audio stream
def get_audio_url(query: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            if "youtube.com" in query or "youtu.be" in query:
                info = ydl.extract_info(query, download=False)
            else:
                info = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}).extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', 'Exclusive Track'), info.get('duration_string', 'MM:SS')
        except Exception as e:
            logger.error(f"YT-DLP Error: {e}")
            return None, None, None

# Inline Control Buttons
def player_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸️ Pause", callback_data="cb_pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="cb_resume"),
                InlineKeyboardButton("⏹️ Stop", callback_data="cb_stop")
            ],
            [
                InlineKeyboardButton("🗑️ Close Panel", callback_data="cb_close")
            ]
        ]
    )

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    welcome_text = (
        f"<b>🎵 Welcome to {Config.BOT_NAME}!</b>\n\n"
        f"<i>An ultra-fast, high-performance Telegram Voice Chat streaming bot.</i>\n\n"
        f"👑 <b>System Status:</b> <code>Online & Secure</code>\n"
        f"⚡ <b>Engine:</b> <code>Pyrogram & PyTgCalls</code>\n\n"
        f"<b>🚀 Commands:</b>\n"
        f"• <code>/play [Song Name / URL]</code> - Stream audio in voice chat\n"
        f"• <code>/pause</code> | <code>/resume</code> | <code>/stop</code> - Control playback\n"
        f"• <code>/ping</code> - Check bot latency"
    )
    await message.reply_text(welcome_text, parse_mode="HTML")

@app.on_message(filters.command("ping"))
async def ping_handler(client, message: Message):
    await message.reply_text("🏓 **Pong!** `{Config.BOT_NAME}` streaming core is running perfectly.", parse_mode="Markdown")

@app.on_message(filters.command("play"))
async def play_handler(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage Error:** Provide a song name or YouTube link!\n\n*Example:* `/play Shape of You`", parse_mode="Markdown")
        return

    query = " ".join(message.command[1:])
    chat_id = message.chat.id

    msg = await message.reply_text("🔍 **Analyzing request & extracting audio stream...**", parse_mode="Markdown")

    audio_url, title, duration = get_audio_url(query)
    if not audio_url:
        await msg.edit("❌ Failed to fetch audio stream. Please check the query!")
        return

    try:
        await call_py.join_group_call(
            chat_id,
            AudioPiped(audio_url)
        )
        
        caption = (
            f"🎶 **Currently Streaming Live via {Config.BOT_NAME}**\n\n"
            f"📌 **Track:** <code>{title}</code>\n"
            f"⏱️ **Duration:** <code>{duration}</code>\n"
            f"⚡ **Status:** <code>Connected to Voice Chat</code>"
        )
        await msg.edit(caption, parse_mode="HTML", reply_markup=player_markup())
    except Exception as e:
        await msg.edit(f"❌ **Stream Execution Error:** `{str(e)}`", parse_mode="Markdown")

@app.on_message(filters.command("pause") & filters.user(Config.SUDO_USERS))
async def pause_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.pause_stream(chat_id)
        await message.reply_text("⏸️ **Stream Paused Successfully!**")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`")

@app.on_message(filters.command("resume") & filters.user(Config.SUDO_USERS))
async def resume_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.resume_stream(chat_id)
        await message.reply_text("▶️ **Stream Resumed Successfully!**")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`")

@app.on_message(filters.command("stop") & filters.user(Config.SUDO_USERS))
async def stop_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.reply_text("⏹️ **Stream Terminated & Left Voice Chat!**")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`")

# Callback Query Handler for Inline Buttons
@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if data in ["cb_pause", "cb_resume", "cb_stop"] and user_id not in Config.SUDO_USERS:
        await callback_query.answer("⚠️️ You are not authorized to use these controls!", show_alert=True)
        return

    try:
        if data == "cb_pause":
            await call_py.pause_stream(chat_id)
            await callback_query.answer("Stream Paused ⏸️")
        elif data == "cb_resume":
            await call_py.resume_stream(chat_id)
            await callback_query.answer("Stream Resumed ▶️")
        elif data == "cb_stop":
            await call_py.leave_group_call(chat_id)
            await callback_query.answer("Stream Stopped ⏹️")
            await callback_query.message.delete()
        elif data == "cb_close":
            await callback_query.message.delete()
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)[:50]}", show_alert=True)

async def main():
    await app.start()
    await call_py.start()
    logger.info(f"🚀 {Config.BOT_NAME} Initialized Successfully!")
    await asyncio.gather()

if __name__ == "__main__":
    app.run(main())
