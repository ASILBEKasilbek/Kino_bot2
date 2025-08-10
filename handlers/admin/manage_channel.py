from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
from database.models import get_all_channels
import sqlite3
from datetime import datetime
import re

# Router
channel_manage_router = Router()

# State for channel management
class ManageChannelForm(StatesGroup):
    channel_id = State()
    action = State()


# Check if channel exists
def channel_exists(channel_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM channels WHERE channel_id = ?", (channel_id,))
        return c.fetchone() is not None

# Validate channel ID format
def is_valid_channel_id(channel_id: str) -> bool:
    return bool(re.match(r"^(@[a-zA-Z0-9_]+|https://t.me/[a-zA-Z0-9_]+|-\d+)$", channel_id))

# Manage channels command (only for admins)
@channel_manage_router.message(Command("manage_channels"))
async def manage_channels_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="add_channel"),
                InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="remove_channel")
            ],
            [InlineKeyboardButton(text="📋 Barcha kanallar", callback_data="list_channels")]
        ]
    )
    await message.reply("📢 Kanallarni boshqarish:", reply_markup=keyboard)

# Handle channel action (add, remove, list)
@channel_manage_router.callback_query(F.data.in_(["add_channel", "remove_channel", "list_channels"]))
async def handle_channel_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Faqat adminlar kanallarni boshqarishi mumkin!", show_alert=True)
        return

    action = callback.data
    await state.update_data(action=action)

    if action == "list_channels":
        channels = get_all_channels()
        if not channels:
            await callback.message.reply("📭 Hozirda hech qanday kanal yo‘q.")
        else:
            channel_list = "\n".join(
                f"🔹 {c}" for c in channels
            )
            await callback.message.reply(f"📋 Faol kanallar:\n{channel_list}")
        await callback.message.delete()
        await callback.answer()
        return

    await state.set_state(ManageChannelForm.channel_id)
    if action == "add_channel":
        await callback.message.reply("➕ Yangi kanal ID’sini kiriting (masalan, @KanalNomi yoki -100123456789):")
    else:
        await callback.message.reply("➖ O‘chiriladigan kanal ID’sini kiriting (masalan, @KanalNomi yoki -100123456789):")
    
    await callback.message.delete()
    await callback.answer()

@channel_manage_router.message(ManageChannelForm.channel_id)
async def process_channel_management(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    data = await state.get_data()
    action = data.get("action", "add_channel")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    gamification = Gamification()

    if action == "add_channel":
        c.execute("INSERT OR IGNORE INTO channels (channel_id) VALUES (?)", (channel_id,))
        conn.commit()
        new_xp = gamification.add_xp(message.from_user.id, "add_channel")
        await message.reply(f"✅ Kanal ({channel_id}) qo‘shildi!\n📊 Yangi XP: {new_xp}")
    else:
        c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
        new_xp = gamification.add_xp(message.from_user.id, "remove_channel")
        await message.reply(f"✅ Kanal ({channel_id}) o‘chirildi!\n📊 Yangi XP: {new_xp}")

    conn.close()
    await state.clear()