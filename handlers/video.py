from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import DB_PATH
from database.models import search_movies
from utils.gamification import Gamification
import sqlite3
from datetime import datetime

search_router = Router()

@search_router.message(Command("search_movie"))
async def search_movie_command(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, qidiruv so‘zini kiriting! Masalan: /search_movie Inception")
        return
    
    query = args[1].strip()
    movies = search_movies(query)
    
    if not movies:
        await message.reply("⚠️ Hech qanday kino topilmadi!")
        return
    
    response = "🎬 Qidiruv natijalari:\n"
    for movie in movies[:5]:
        movie_id, _, title, genre, year, description, is_premium, _ = movie
        response += f"📽 {title} ({year}) - {genre}\n💎 Premium: {'Ha' if is_premium else 'Yo‘q'}\n📜 {description}\n🔗 Kod: {movie[1]}\n\n"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "request_recommendation")
    
    await message.reply(f"{response}📊 Yangi XP: {new_xp}")
