import sqlite3
import re
from aiogram import Bot
from config import DB_PATH
from aiogram.exceptions import TelegramAPIError
import re
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

async def check_subscription_status(bot: Bot, user_id: int, channel_id: str) -> bool:
    try:
        chat_id = str(channel_id).strip()

        # Kanal ID formatlash (-100 bilan bo‘lmasa qo‘shamiz)
        if re.match(r"^\d{9,}$", chat_id) and not chat_id.startswith("-100"):
            chat_id = f"-100{chat_id}"

        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)

        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest:
        return False  # foydalanuvchi topilmadi yoki kanal noto‘g‘ri
    except TelegramAPIError:
        return False  # API xato bo‘lsa ham a’zo emas deb hisoblaymiz
    except Exception:
        return False

# async def check_subscription_status(bot: Bot, user_id: int, channel: str = "") -> bool:
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     try:
#         cursor.execute("SELECT channel_id FROM channels")
#         rows = cursor.fetchall()
#         channel_ids = [row[0] for row in rows]
#     finally:
#         conn.close()


#     for ch in channel_ids:
#         ch_str = str(ch).strip()

#         # 1️⃣ Agar kanal zayavka link bo'lsa (https://t.me/+...)
#         # if ch_str.startswith("https://t.me/+"):
#             # if not await _check_join_request(user_id, ch_str):
#             #     print(f"❌ {user_id} zayavka kanalga qo'shilmagan: {ch_str}")
#             #     return True
#             # else:
#             #     print(f"✅ {user_id} zayavka kanalga qo'shilgan: {ch_str}")
#             #     continue

#         # 2️⃣ Oddiy kanallarni API orqali tekshirish
#         try:
#             chat_id = ch_str
#             # Agar faqat raqam bo'lsa va -100 bilan boshlanmasa
#             if re.match(r"^\d{9,}$", chat_id) and not chat_id.startswith("-100"):
#                 chat_id = f"-100{chat_id}"

#             member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
#             if member.status not in ("member", "administrator", "creator"):
#                 return False

#         except TelegramAPIError as e:
#             return True  # API muammosida bloklamaymiz
#         except Exception as e:
#             return False

#     return True


async def _check_join_request(user_id: int, channel: str) -> bool:
    """Bazadan foydalanuvchi zayavka kanalga qo'shilganmi, tekshiradi"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 1 FROM join_confirmations 
            WHERE user_id = ? AND channel = ? AND is_joined = 1
        """, (user_id, channel))
        result = cursor.fetchone()
    finally:
        conn.close()

    return result is not None


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
        return False
    finally:
        conn.close()
    return True
