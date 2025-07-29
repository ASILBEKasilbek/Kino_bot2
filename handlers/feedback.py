from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import DB_PATH, ADMIN_IDS
from utils.gamification import Gamification
from datetime import datetime
import sqlite3

feedback_router = Router()

class FeedbackForm(StatesGroup):
    text = State()

@feedback_router.message(Command("feedback"))
async def feedback_command(message: Message, state: FSMContext):
    await state.set_state(FeedbackForm.text)
    await message.reply("✍️ Iltimos, fikr-mulohazangizni yozing:")

@feedback_router.message(FeedbackForm.text)
async def process_feedback(message: Message, state: FSMContext):
    feedback_text = message.text.strip()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, feedback_text, submitted_at) VALUES (?, ?, ?)",
              (message.from_user.id, feedback_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "leave_feedback")
    
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(admin_id, f"🔔 Yangi fikr-mulohaza (ID: {message.from_user.id}): {feedback_text}")
    
    await message.reply(f"✅ Fikr-mulohazangiz yuborildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()