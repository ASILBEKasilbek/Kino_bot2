import sqlite3
from aiogram import Bot
from config import DB_PATH

from aiogram.exceptions import TelegramAPIError

async def check_subscription_status(bot: Bot, user_id: int, channel: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT channel_id FROM channels")
        rows = cursor.fetchall()
        channel_ids = [row[0] for row in rows]
    finally:
        conn.close()
    print(f"👤 Foydalanuvchi {user_id} uchun kanallar: {channel_ids}")
    for channel in channel_ids:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                print(f"❌ {user_id} obuna emas: {channel}")
                return False
        except TelegramAPIError as e:
            print(f"❌ Telegram API xatoligi: {e} — kanal: {channel}")
            return True
        except Exception as e:
            print(f"⚠️ Boshqa xatolik: {e}")
            return False
        print(f"✅ {user_id} kanalga obuna: {channel}")

    return True

# async def check_subscription_status(bot: Bot, user_id: int, channel: str) -> bool:
#     print("Channel23:", channel)

#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
#         # Faqat SELECT bo'lishi kerak
#         cursor.execute(
#             "SELECT 1 FROM join_confirmations WHERE user_id = ? AND channel = ? AND is_joined = 1",
#             (user_id, channel)
#         )
#         result = cursor.fetchone()
#     except sqlite3.Error as e:
#         print(f"❌ Database xatosi: {e}")
#         return True 
#     finally:
#         conn.close()

#     print(f"👤 Foydalanuvchi {user_id} kanal {channel} uchun 'Join' bosganligini tekshirish: {result}")
#     return result is not None

async def confirm_join(bot: Bot, user_id: int, channel: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO join_confirmations (user_id, channel, is_joined, created_at) VALUES (?, ?, 1, datetime('now'))",
            (user_id, channel)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database xatosi: {e}")
        return False
    finally:
        conn.close()

    print(f"👤 Foydalanuvchi {user_id} kanal {channel} uchun 'Join' ni tasdiqladi")
    return True
