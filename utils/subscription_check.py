import sqlite3
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from config import DB_PATH

async def check_subscription_status(bot: Bot, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT channel_id FROM channels")
        rows = cursor.fetchall()
        channel_ids = [row[0] for row in rows]
    finally:
        conn.close()

    for channel in channel_ids:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                print(f"❌ {user_id} obuna emas: {channel}")
                return False
        except TelegramAPIError as e:
            print(f"❌ Telegram API xatoligi: {e} — kanal: {channel}")
            return False
        except Exception as e:
            print(f"⚠️ Boshqa xatolik: {e}")
            return False

    return True
