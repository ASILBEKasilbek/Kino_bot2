from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from database.models import get_all_channels
import sqlite3
import re

channel_manage_router = Router()

# --- FSM holati ---
class ManageChannelForm(StatesGroup):
    action = State()
    channel_id = State()
    channel_link = State()

# --- Tekshiruvlar ---
def channel_exists(channel_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM channels WHERE channel_id = ?", (channel_id,))
        return c.fetchone() is not None

def is_valid_channel_id(channel_id: str) -> bool:
    return bool(re.match(r"^(@[a-zA-Z0-9_]+|https://t.me/[a-zA-Z0-9_]+|-\d+)$", channel_id))

# --- Yordamchi funksiyalar ---
async def add_channel_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManageChannelForm.action)
    await callback.message.edit_text(
        "➕ Yangi kanal ID’sini kiriting (masalan, @KanalNomi yoki -100123456789):"
    )
    await callback.answer()

async def list_channels(callback: CallbackQuery):
    channels = get_all_channels()
    if not channels:
        await callback.message.edit_text("📭 Hozirda hech qanday kanal yo‘q.")
        await callback.answer()
        return

    msg_text = "📋 Faol kanallar:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"🔗 {c[0]}", url=c[1])] for c in channels]
    )
    await callback.message.edit_text(msg_text, reply_markup=keyboard)
    await callback.answer()

async def remove_channel_prompt(callback: CallbackQuery):
    channels = get_all_channels()
    if not channels:
        await callback.message.edit_text("📭 Hozirda hech qanday kanal yo‘q.")
        await callback.answer()
        return

    msg_text = "📋 Faol kanallar:\n❌ Tugmani bosib kanalni o‘chiring:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"❌ {c[0]}", callback_data=f"delete_{c[0]}")] for c in channels]
    )
    await callback.message.edit_text(msg_text, reply_markup=keyboard)
    await callback.answer()

def generate_channel_link(channel_id: str) -> str:
    """Kanal ID asosida link hosil qiladi"""
    if channel_id.startswith("@"):
        return f"https://t.me/{channel_id.lstrip('@')}"
    elif channel_id.startswith("https://t.me/"):
        return channel_id
    else:  # -100123456789 shakli
        return f"https://t.me/c/{channel_id.lstrip('-100')}/1"

# --- Admin panel buyruq ---
@channel_manage_router.message(Command("manage_channels"))
async def manage_channels_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="add_channel")],
            [InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="remove_channel")],
            [InlineKeyboardButton(text="📋 Barcha kanallar", callback_data="list_channels")]
        ]
    )
    await message.reply("📢 Kanallarni boshqarish:", reply_markup=keyboard)

# --- Inline tugma orqali harakat ---
@channel_manage_router.callback_query(F.data.in_(["remove_channel", "list_channels"]))
async def handle_channel_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Faqat adminlar kanallarni boshqarishi mumkin!", show_alert=True)
        return

    action = callback.data

    if action == "list_channels":
        await list_channels(callback)
    elif action == "remove_channel":
        await remove_channel_prompt(callback)

@channel_manage_router.callback_query(F.data == "add_channel")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📢 Kanal ID ni kiriting (masalan: `-1001234567890`):")
    await state.set_state(ManageChannelForm.channel_id)
    await callback.answer()  # spinnerni yo‘qotish

# --- 4. Kanal ID qabul qilinadi ---
@channel_manage_router.message(ManageChannelForm.channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    await message.answer("🔗 Endi kanal linkini kiriting (masalan: https://t.me/yourchannel):")
    await state.set_state(ManageChannelForm.channel_link)

@channel_manage_router.message(ManageChannelForm.channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data["channel_id"]
    channel_link = message.text.strip()

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO channels (channel_id, channel_link)
            VALUES (?, ?)
        """, (channel_id, channel_link))
        conn.commit()

    await message.answer(f"✅ Kanal muvaffaqiyatli qo‘shildi!\n🆔 ID: {channel_id}\n🔗 Link: {channel_link}")
    await state.clear()

# --- Kanal qo‘shish (FSM handler) ---
@channel_manage_router.message(ManageChannelForm.action)
async def process_add_channel(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    channel_link = generate_channel_link(channel_id)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_link) VALUES (?, ?)",
            (channel_id, channel_link)
        )
        conn.commit()

    await message.reply(f"✅ Kanal ({channel_id}) qo‘shildi!\n🔗 Link: {channel_link}")
    await state.clear()

# --- Inline tugma orqali kanal o‘chirish ---
@channel_manage_router.callback_query(F.data.startswith("delete_"))
async def delete_channel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Faqat adminlar kanallarni o‘chira oladi!", show_alert=True)
        return

    channel_id = callback.data.split("delete_")[1]
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()

    await callback.message.edit_text(f"✅ Kanal ({channel_id}) o‘chirildi!", reply_markup=None)
    await callback.answer("Kanal o‘chirildi!")
