from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import DB_PATH, PAYME_TOKEN, CLICK_TOKEN, APELSIN_TOKEN
from datetime import datetime, timedelta
import sqlite3
from utils.gamification import Gamification
from core.payment import process_payment
from aiogram.types import CallbackQuery
subscription_router = Router()

@subscription_router.message(Command("buy_subscription"))
async def buy_subscription_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme", callback_data="payme"),
         InlineKeyboardButton(text="💳 Click", callback_data="click"),
         InlineKeyboardButton(text="💳 Apelsin", callback_data="apelsin")]
    ])
    await message.reply("💎 Obuna rejasini tanlang:", reply_markup=keyboard)

@subscription_router.callback_query(F.data.in_(["payme", "click", "apelsin"]))
async def process_payment_selection(callback: CallbackQuery):
    payment_method = callback.data
    token = {"payme": PAYME_TOKEN, "click": CLICK_TOKEN, "apelsin": APELSIN_TOKEN}[payment_method]
    
    payment_url = await process_payment(callback.from_user.id, payment_method, token)
    if not payment_url:
        await callback.message.reply("⚠️ To‘lov tizimida xatolik!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 To‘lov qilish", url=payment_url)]
    ])
    await callback.message.reply(f"✅ {payment_method.capitalize()} orqali to‘lov qiling:", reply_markup=keyboard)
    await callback.message.delete()

@subscription_router.message(Command("check_subscription"))
async def check_subscription_command(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT subscription_plan, subscription_expiry FROM users WHERE user_id = ?", (message.from_user.id,))
    user = c.fetchone()
    conn.close()
    
    if user and user[0] and user[1] and datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S") > datetime.now():
        await message.reply(f"💎 Sizning obunangiz: {user[0]}\n📅 Muddati: {user[1]}")
    else:
        await message.reply("⚠️ Sizda faol obuna yo‘q! /buy_subscription")