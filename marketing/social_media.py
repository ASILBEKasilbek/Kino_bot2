from aiogram import Router, F
from aiogram.types import Message
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
import sqlite3
from datetime import datetime

social_media_router = Router()

@social_media_router.message(commands=["social_post"])
async def social_post_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Faqat adminlar ijtimoiy tarmoqqa post joylashi mumkin!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, post matnini kiriting! Masalan: /social_post Yangi kino chiqdi!")
        return
    
    content = args[1]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO social_posts (user_id, content, posted_at) VALUES (?, ?, ?)",
              (message.from_user.id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "social_post")
    
    await message.reply(f"📢 Post ijtimoiy tarmoqlarga joylandi!\n📊 Yangi XP: {new_xp}")
