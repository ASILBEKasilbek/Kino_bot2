from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
import sqlite3
from aiogram.types import CallbackQuery
channel_manage_router = Router()

class ManageChannelForm(StatesGroup):
    channel_id = State()

@channel_manage_router.message(Command("manage_channels"))
async def manage_channels_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="add_channel"),
         InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="remove_channel")]
    ])
    await message.reply("📢 Kanallarni boshqarish:", reply_markup=keyboard)

@channel_manage_router.callback_query(F.data == "add_channel")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManageChannelForm.channel_id)
    await callback.message.reply("➕ Yangi kanal ID’sini kiriting (masalan, @KanalNomi):")
    await callback.message.delete()

@channel_manage_router.callback_query(F.data == "remove_channel")
async def remove_channel_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManageChannelForm.channel_id)
    await callback.message.reply("➖ O‘chiriladigan kanal ID’sini kiriting (masalan, @KanalNomi):")
    await callback.message.delete()

@channel_manage_router.message(ManageChannelForm.channel_id)
async def process_channel_management(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    
    action = (await state.get_data()).get("action", "add_channel")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if action == "add_channel":
        c.execute("INSERT OR IGNORE INTO channels (channel_id) VALUES (?)", (channel_id,))
        conn.commit()
        gamification = Gamification()
        new_xp = gamification.add_xp(message.from_user.id, "add_channel")
        await message.reply(f"✅ Kanal ({channel_id}) qo‘shildi!\n📊 Yangi XP: {new_xp}")
    else:
        c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
        gamification = Gamification()
        new_xp = gamification.add_xp(message.from_user.id, "remove_channel")
        await message.reply(f"✅ Kanal ({channel_id}) o‘chirildi!\n📊 Yangi XP: {new_xp}")
    
    conn.close()
    await state.clear()