from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import DB_PATH, PAYME_TOKEN, CLICK_TOKEN, APELSIN_TOKEN
from utils.gamification import Gamification
from datetime import datetime, timedelta
import sqlite3
import requests

process_payment = Router()

class PaymentForm(StatesGroup):
    plan = State()
    provider = State()

@process_payment.message(Command("buy_subscription"))
async def buy_subscription_command(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 kun ($1)", callback_data="plan_daily"),
         InlineKeyboardButton(text="1 hafta ($3)", callback_data="plan_weekly")],
        [InlineKeyboardButton(text="1 oy ($5)", callback_data="plan_monthly")]
    ])
    await message.answer("💎 Obuna rejasini tanlang:", reply_markup=keyboard)
    await state.set_state(PaymentForm.plan)

@process_payment.callback_query(PaymentForm.plan, F.data.startswith("plan_"))
async def process_plan_selection(callback: CallbackQuery, state: FSMContext):
    plan = callback.data.split("_")[1]
    price = {"daily": 100, "weekly": 300, "monthly": 500}[plan]
    duration = {"daily": 1, "weekly": 7, "monthly": 30}[plan]
    
    await state.update_data(plan=plan, price=price, duration=duration)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Payme", callback_data="provider_payme"),
         InlineKeyboardButton(text="Click", callback_data="provider_click"),
         InlineKeyboardButton(text="Apelsin", callback_data="provider_apelsin")]
    ])
    await callback.message.answer("💳 To‘lov usulini tanlang:", reply_markup=keyboard)
    await state.set_state(PaymentForm.provider)
    await callback.message.delete()

@process_payment.callback_query(PaymentForm.provider, F.data.startswith("provider_"))
async def process_provider_selection(callback: CallbackQuery, state: FSMContext):
    provider = callback.data.split("_")[1]
    user_data = await state.get_data()
    plan = user_data["plan"]
    price = user_data["price"]
    duration = user_data["duration"]
    
    token = {"payme": PAYME_TOKEN, "click": CLICK_TOKEN, "apelsin": APELSIN_TOKEN}[provider]

    # To‘lov so‘rovi (mock API uchun)
    try:
        response = requests.post(
            f"https://{provider}.uz/api/create",
            json={"amount": price, "user_id": callback.from_user.id, "token": token},
            timeout=5
        )
    except requests.exceptions.RequestException:
        await callback.message.answer("❌ To‘lov xizmatiga ulanishda xatolik yuz berdi.")
        await state.clear()
        await callback.message.delete()
        return
    
    if response.status_code == 200:
        subscription_end = (datetime.now() + timedelta(days=duration)).strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE users SET subscription_plan = ?, subscription_end = ? 
            WHERE user_id = ?
        """, (plan, subscription_end, callback.from_user.id))
        conn.commit()
        conn.close()
        
        gamification = Gamification()
        new_xp = gamification.add_xp(callback.from_user.id, "purchase_subscription")
        
        await callback.message.answer(
            f"🎉 Obuna muvaffaqiyatli sotib olindi! ({plan})\n"
            f"⏳ Tugash sanasi: {subscription_end}\n"
            f"📊 Yangi XP: {new_xp}"
        )
    else:
        await callback.message.answer("⚠️ To‘lovda xatolik yuz berdi!")

    await state.clear()
    await callback.message.delete()
