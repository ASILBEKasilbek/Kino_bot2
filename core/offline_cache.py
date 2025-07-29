from aiogram import Router, F
from aiogram.types import Message
from config import DB_PATH
from database.models import get_movie_by_code
from utils.gamification import Gamification
from datetime import datetime, timedelta
import sqlite3

offline_cache_router = Router()

def add_to_cache(user_id: int, movie_id: int, file_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    expiry = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO offline_cache (user_id, file_id, movie_id, expiry) VALUES (?, ?, ?, ?)",
              (user_id, file_id, movie_id, expiry))
    conn.commit()
    conn.close()

def clear_expired_cache():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM offline_cache WHERE expiry < ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    conn.commit()
    conn.close()

@offline_cache_router.message(commands=["cache_movie"])
async def cache_movie_command(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, kino kodini kiriting! Masalan: /cache_movie KINO987")
        return
    
    movie_code = args[1].upper()
    movie = get_movie_by_code(movie_code)
    
    if not movie:
        await message.reply("⚠️ Bunday kino kodi topilmadi!")
        return
    
    movie_id, file_id, _, title, _, _, _, is_premium, _ = movie
    if is_premium:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT subscription_plan, subscription_end FROM users WHERE user_id = ?", (message.from_user.id,))
        user = c.fetchone()
        conn.close()
        
        if not user or user[0] is None or (user[1] and datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S") < datetime.now()):
            await message.reply("🚫 Bu premium kino! Iltimos, premium obuna sotib oling.")
            return
    
    add_to_cache(message.from_user.id, movie_id, file_id)
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "cache_movie")
    
    await message.reply(f"💾 {title} offline keshga qo‘shildi! 24 soat ichida ko‘rishingiz mumkin.\n📊 Yangi XP: {new_xp}")
