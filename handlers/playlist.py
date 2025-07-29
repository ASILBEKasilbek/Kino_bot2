from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import DB_PATH
from utils.gamification import Gamification
from datetime import datetime
import sqlite3
from aiogram.types import CallbackQuery


playlist_router = Router()

class PlaylistForm(StatesGroup):
    name = State()
    movie_code = State()

@playlist_router.message(Command("create_playlist"))
async def create_playlist_command(message: Message, state: FSMContext):
    await state.set_state(PlaylistForm.name)
    await message.reply("📋 Pleylist nomini kiriting:")

@playlist_router.message(PlaylistForm.name)
async def process_playlist_name(message: Message, state: FSMContext):
    playlist_name = message.text.strip()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO playlists (user_id, name, created_at) VALUES (?, ?, ?)",
              (message.from_user.id, playlist_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "create_playlist")
    
    await message.reply(f"✅ Pleylist '{playlist_name}' yaratildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()

@playlist_router.message(Command("add_to_playlist"))
async def add_to_playlist_command(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, kino kodini kiriting! Masalan: /add_to_playlist KINO123")
        return
    
    await state.set_state(PlaylistForm.movie_code)
    await state.update_data(movie_code=args[1].strip().upper())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM playlists WHERE user_id = ?", (message.from_user.id,))
    playlists = c.fetchall()
    conn.close()
    
    if not playlists:
        await message.reply("⚠️ Sizda pleylist yo‘q! /create_playlist")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"playlist_{id}") for id, name in playlists]
    ])
    await message.reply("📋 Qaysi pleylistga qo‘shmoqchisiz?", reply_markup=keyboard)

@playlist_router.callback_query(F.data.startswith("playlist_"))
async def process_playlist_selection(callback: CallbackQuery, state: FSMContext):
    playlist_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    movie_code = user_data["movie_code"]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM movies WHERE movie_code = ?", (movie_code,))
    movie = c.fetchone()
    
    if not movie:
        await callback.message.reply("⚠️ Kino topilmadi!")
        conn.close()
        return
    
    c.execute("INSERT INTO playlist_movies (playlist_id, movie_id) VALUES (?, ?)", (playlist_id, movie[0]))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(callback.from_user.id, "add_to_playlist")
    
    await callback.message.reply(f"✅ Kino pleylistga qo‘shildi!\n📊 Yangi XP: {new_xp}")
    await callback.message.delete()
    await state.clear()