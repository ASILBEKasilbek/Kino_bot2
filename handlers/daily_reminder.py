import random
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import DB_PATH, BOT_TOKEN
from core.ai_recommendation import get_movie_recommendations
import sqlite3
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
reminder_router = Router()
scheduler = AsyncIOScheduler()

async def send_daily_reminder():
    bot = Bot(token=BOT_TOKEN)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_blocked = 0")
    users = c.fetchall()
    conn.close()
    
    for user in users:
        user_id = user[0]
        recommendations = get_movie_recommendations(user_id)
        if recommendations:
            movie = random.choice(recommendations)
            file_id = movie[1]
            movie_id, title, genre, year, description = movie
            try:

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="📢 Barcha kodlar", callback_data="barcha_kinolar")
                        ]
                    ]
                )
                caption = (
                    f"📽 Bugungi kino tavsiyasi: \n"
                    f"🎬 <b>{title}</b> ({year})\n"
                    f"🎭 <b>Janr:</b> {genre}\n"
                    f"📝 <b>Tavsif:</b>\n{description}\n\n"
                )
                await bot.send_video(
                    chat_id=user_id,
                    video=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except:
                continue
    
    await bot.close()

def setup_scheduler():
    scheduler.add_job(
        send_daily_reminder,
        trigger="cron",
        hour=9,
        minute=0,
        second=0
    )
    scheduler.start()

@reminder_router.message(Command("enable_reminder"))
async def enable_reminder_command(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    conn.close()
    
    await message.reply("🔔 Kunlik kino eslatmalari yoqildi!")
