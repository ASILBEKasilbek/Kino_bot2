from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import DB_PATH
from utils.token_generator import TokenGenerator
from utils.gamification import Gamification
from datetime import datetime
import sqlite3

referral_router = Router()

@referral_router.message(Command("referral"))
async def referral_command(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT referral_code FROM users WHERE user_id = ?", (message.from_user.id,))
    user = c.fetchone()
    
    if not user or not user[0]:
        referral_code = TokenGenerator.generate_referral_code()
        c.execute("UPDATE users SET referral_code = ? WHERE user_id = ?",
                  (referral_code, message.from_user.id))
        conn.commit()
    else:
        referral_code = user[0]
    
    c.execute("SELECT referral_count FROM users WHERE user_id = ?", (message.from_user.id,))
    referral_count = c.fetchone()[0] or 0
    conn.close()
    
    referral_link = f"https://t.me/KinoBotProPlus?start={referral_code}"
    await message.reply(
        f"🤝 Sizning referal havolangiz: {referral_link}\n"
        f"📊 Hozirgi referallar: {referral_count}\n"
        f"Do‘stlaringizni taklif qiling va bonus oling!"
    )

@referral_router.message(Command("start"), F.text.contains(" "))
async def process_referral(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return
    
    referral_code = args[1].strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referral_code,))
    referrer = c.fetchone()
    
    if referrer and referrer[0] != message.from_user.id:
        gamification = Gamification()
        await gamification.award_referral_bonus(message.bot, referrer[0], message.from_user.id)
        await message.reply("🎉 Referal muvaffaqiyatli ro‘yxatdan o‘tdi!")
    
    conn.close()