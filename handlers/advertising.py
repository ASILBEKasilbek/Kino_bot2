from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from datetime import datetime
import sqlite3

advertising_router = Router()

@advertising_router.message(Command("send_ad"))
async def send_ad_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, reklama matnini kiriting! Masalan: /send_ad Yangi kino chiqdi!")
        return
    
    ad_content = args[1]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_blocked = 0")
    users = c.fetchall()
    conn.close()
    
    for user in users:
        try:
            await message.bot.send_message(user[0], f"📢 Reklama: {ad_content}")
        except:
            continue
    
    await message.reply("✅ Reklama barcha foydalanuvchilarga yuborildi!")