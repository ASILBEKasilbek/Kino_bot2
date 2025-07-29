from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command  # ✅ Aiogram 3.x uchun
from config import DB_PATH
from utils.gamification import Gamification
import sqlite3
from typing import List, Tuple

recommendation_router = Router()

def get_movie_recommendations(user_id: int, genre: str = None, year: int = None) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Foydalanuvchi tarixiga asoslangan tavsiya
    c.execute("SELECT movie_id FROM feedback WHERE user_id = ?", (user_id,))
    watched_movies = [row[0] for row in c.fetchall()]
    
    query = "SELECT id, title, genre, year, description FROM movies WHERE 1=1"
    params = []
    
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    if year:
        query += " AND year = ?"
        params.append(year)
    if watched_movies:
        query += " AND id NOT IN ({})".format(",".join("?" * len(watched_movies)))
        params.extend(watched_movies)
    
    query += " ORDER BY view_count DESC LIMIT 5"
    c.execute(query, params)
    recommendations = c.fetchall()
    conn.close()
    return recommendations

@recommendation_router.message(Command("recommend"))  # ✅ to'g'rilandi
async def recommend_command(message: Message):
    args = message.text.split(maxsplit=1)
    genre, year = None, None
    if len(args) > 1:
        params = args[1].split()
        for param in params:
            if param.isdigit():
                year = int(param)
            else:
                genre = param
    
    recommendations = get_movie_recommendations(message.from_user.id, genre, year)
    if not recommendations:
        await message.reply("⚠️ Tavsiya topilmadi! Boshqa janr yoki yil kiriting.")
        return
    
    response = "🎬 Tavsiya etilgan kinolar:\n\n"
    for movie in recommendations:
        movie_id, title, genre, year, description = movie
        response += f"📽 {title} ({year})\n🎭 Janr: {genre}\n📜 Tavsif: {description}\n\n"
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "request_recommendation")
    response += f"📊 Yangi XP: {new_xp}"
    
    await message.reply(response)
