from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import DB_PATH, ADMIN_IDS
from utils.gamification import Gamification
from datetime import datetime
import sqlite3

upcoming_router = Router()

class UpcomingMovieForm(StatesGroup):
    title = State()
    release_date = State()

@upcoming_router.message(Command("upcoming"))
async def upcoming_command(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, release_date FROM upcoming_movies WHERE release_date >= ?",
              (datetime.now().strftime("%Y-%m-%d"),))
    movies = c.fetchall()
    conn.close()
    
    if not movies:
        await message.reply("⚠️ Hozirda kutilayotgan kinolar yo‘q!")
        return
    
    response = "🎬 Kutilayotgan kinolar:\n"
    for title, release_date in movies:
        response += f"📽 {title} - {release_date}\n"
    
    await message.reply(response)

@upcoming_router.message(Command("add_upcoming"))
async def add_upcoming_command(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Faqat adminlar kino qo‘shishi mumkin!")
        return
    
    await state.set_state(UpcomingMovieForm.title)
    await message.reply("📽 Kino nomini kiriting:")

@upcoming_router.message(UpcomingMovieForm.title)
async def process_upcoming_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(UpcomingMovieForm.release_date)
    await message.reply("📅 Chiqish sanasini kiriting (YYYY-MM-DD):")

@upcoming_router.message(UpcomingMovieForm.release_date)
async def process_upcoming_release_date(message: Message, state: FSMContext):
    try:
        release_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.reply("⚠️ Sana formati YYYY-MM-DD bo‘lishi kerak!")
        return
    
    user_data = await state.get_data()
    title = user_data["title"]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO upcoming_movies (title, release_date, added_by) VALUES (?, ?, ?)",
              (title, release_date.strftime("%Y-%m-%d"), message.from_user.id))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "add_upcoming_movie")
    
    await message.reply(f"✅ '{title}' kutilayotgan kinolar ro‘yxatiga qo‘shildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()
