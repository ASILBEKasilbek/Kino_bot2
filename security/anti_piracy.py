from aiogram import Router, F
from aiogram.types import Message
from config import DB_PATH, ADMIN_IDS
from datetime import datetime, timedelta
import sqlite3

anti_piracy_router = Router()

@anti_piracy_router.message()
async def monitor_activity(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message_count, last_message_time FROM users WHERE user_id = ?", (message.from_user.id,))
    user = c.fetchone()
    
    current_time = datetime.now()
    message_count = user[0] if user else 0
    last_message_time = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S") if user and user[1] else current_time - timedelta(seconds=10)
    
    if (current_time - last_message_time).total_seconds() < 2:
        message_count += 1
    else:
        message_count = 1
    
    c.execute("UPDATE users SET message_count = ?, last_message_time = ? WHERE user_id = ?",
              (message_count, current_time.strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    
    if message_count > 5:
        c.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (message.from_user.id,))
        conn.commit()
        for admin_id in ADMIN_IDS:
            await message.bot.send_message(admin_id, f"🚨 Foydalanuvchi {message.from_user.id} piratlik tufayli bloklandi!")
        await message.reply("🚫 Siz piratlik tufayli bloklandingiz!")
    
    conn.close()
