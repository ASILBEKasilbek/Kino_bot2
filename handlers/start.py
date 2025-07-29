from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import DB_PATH, CHANNEL_IDS, BOT_TOKEN
from utils.subscription_check import check_subscription_status
from datetime import datetime
import sqlite3
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_router = Router()

# @start_router.message(Command("start"))
# async def start_command(message: Message):
#     bot = Bot(token=BOT_TOKEN)
#     user_id = message.from_user.id
#     username = message.from_user.username or "No username"
    
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("INSERT OR IGNORE INTO users (user_id, username, registration_date, last_activity) VALUES (?, ?, ?, ?)",
#               (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#     conn.commit()
#     conn.close()
    
#     is_subscribed = await check_subscription_status(bot, user_id)
#     if not is_subscribed:
#         channel_links = "\n".join([f"📢 <a href='https://t.me/{channel}'>Kanal</a>" for channel in CHANNEL_IDS])
#         await message.reply(
#             f"👋 Xush kelibsiz, {username}!\n"
#             f"KinoBot Pro++ ga xush kelibsiz! Kino olish uchun quyidagi kanallarga obuna bo‘ling:\n{channel_links}",
#             parse_mode="HTML"
#         )
#         await bot.close()
#         return
    

#     # keyboard = InlineKeyboardMarkup(
#         # inline_keyboard=[
#             # [
#                 # InlineKeyboardButton(text="🎬 Kino kodlari", callback_data="get_video"),]
#             #     InlineKeyboardButton(text="🤖 AI tavsiyasi", callback_data="recommend")
#             # ],
#             # [
#             #     InlineKeyboardButton(text="💎 Premium obuna", callback_data="buy_subscription"),
#             #     InlineKeyboardButton(text="👥 Do‘st taklif qilish", callback_data="referral")
#             # ]
#         # ]
#     # )


#     # await message.answer(
#     #     f"🎬 <b>KinoBot Pro++</b> ga xush kelibsiz, <b>{username}</b>!\n\n"
#     #     f"Botimiz orqali eng so‘nggi kinolarni olish, AI tavsiyalarini olish, premium obunani sotib olish va do‘stlaringizni taklif qilish imkoniyatiga egasiz.\n\n"    
#     #     f"Kino kodini yuboring yoki quyidagi tugmalardan foydalaning:\n\n",
#     #     reply_markup=keyboard,
#     #     parse_mode="HTML"
#     # )
#     await message.answer(f"🎬 <b>KinoBot</b> ga xush kelibsiz, <b>{username}</b>!\n\n iltimos kod yuboring",parse_mode="HTML")
    
from aiogram.types import CallbackQuery

@start_router.callback_query(F.data == "recommend")
async def process_get_video_callback(callback: CallbackQuery):
    await callback.message.answer("🛠Bu funksiya yaqin kunlarda ishga tushadi,hozircha texnik xizmatda", parse_mode="Markdown")


@start_router.callback_query(F.data == "buy_subscription")
async def process_get_video_callback(callback: CallbackQuery):
    await callback.message.answer("🛠Bu funksiya yaqin kunlarda ishga tushadi,hozircha texnik xizmatda", parse_mode="Markdown")

@start_router.callback_query(F.data == "referral")
async def process_get_video_callback(callback: CallbackQuery):
    await callback.message.answer("🛠Bu funksiya yaqin kunlarda ishga tushadi,hozircha texnik xizmatda", parse_mode="Markdown")
