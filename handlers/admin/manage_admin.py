from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
import sqlite3
from aiogram.types import CallbackQuery
admin_manage_router = Router()

class ManageAdminForm(StatesGroup):
    user_id = State()

@admin_manage_router.message(Command("manage_admins"))
async def manage_admins_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat super adminlar uchun!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo‘shish", callback_data="add_admin"),
         InlineKeyboardButton(text="➖ Admin o‘chirish", callback_data="remove_admin")]
    ])
    await message.reply("🎛 Adminlarni boshqarish:", reply_markup=keyboard)

@admin_manage_router.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManageAdminForm.user_id)
    await callback.message.reply("➕ Yangi admin ID’sini kiriting:")
    await callback.message.delete()

@admin_manage_router.callback_query(F.data == "remove_admin")
async def remove_admin_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManageAdminForm.user_id)
    await callback.message.reply("➖ O‘chiriladigan admin ID’sini kiriting:")
    await callback.message.delete()

@admin_manage_router.message(ManageAdminForm.user_id)
async def process_admin_management(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.reply("⚠️ ID raqam bo‘lishi kerak!")
        return
    
    action = (await state.get_data()).get("action", "add_admin")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if action == "add_admin":
        c.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        gamification = Gamification()
        new_xp = gamification.add_xp(message.from_user.id, "add_admin")
        await message.reply(f"✅ Foydalanuvchi (ID: {user_id}) admin qilindi!\n📊 Yangi XP: {new_xp}")
    else:
        c.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        gamification = Gamification()
        new_xp = gamification.add_xp(message.from_user.id, "remove_admin")
        await message.reply(f"✅ Foydalanuvchi (ID: {user_id}) adminlikdan olindi!\n📊 Yangi XP: {new_xp}")
    
    conn.close()
    await state.clear()