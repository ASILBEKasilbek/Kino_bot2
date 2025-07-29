from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
from datetime import datetime
import sqlite3
import logging

ad_router = Router()

@ad_router.message(Command("send_ad"))
async def admin_send_ad_command(message: Message):
    # Admin tekshiruvi
    print(f"Admin {message.from_user.id} so'rov yubordi: {message.text}")
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return

    # Reklama matni borligini tekshirish
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Iltimos, reklama matnini kiriting!\nMisol: /send_ad Yangi kino chiqdi!")
        return

    ad_content = args[1]

    # Foydalanuvchilar ro'yxatini olish
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_blocked = 0")
        users = c.fetchall()
        conn.close()
    except Exception as e:
        logging.error(f"❌ Foydalanuvchilarni olishda xatolik: {e}")
        await message.reply("❌ Foydalanuvchilar ro'yxatini olishda xatolik yuz berdi.")
        return

    # Reklama yuborish
    success_count = 0
    for (user_id,) in users:
        try:
            await message.bot.send_message(user_id, f"📢 Reklama: {ad_content}")
            success_count += 1
        except Exception as e:
            logging.warning(f"⚠️ Xabar yuborilmadi: user_id={user_id}, error={e}")
            continue

    # XP qo'shish
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "send_ad")

    # Javob
    await message.reply(
        f"✅ Reklama {success_count} ta foydalanuvchiga yuborildi!\n"
        f"📊 Yangi XP: {new_xp}"
    )
