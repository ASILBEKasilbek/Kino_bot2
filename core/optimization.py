from aiogram import Router, F
from aiogram.types import Message
from config import DB_PATH, ADMIN_IDS
from utils.gamification import Gamification
import sqlite3

optimization_router = Router()

@optimization_router.message(commands=["optimize_db"])
async def optimize_db_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Faqat adminlar ma'lumotlar bazasini optimallashtirishi mumkin!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("VACUUM")
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "optimize_db")
    
    await message.reply(f"🛠 Ma'lumotlar bazasi optimallashtirildi!\n📊 Yangi XP: {new_xp}")
