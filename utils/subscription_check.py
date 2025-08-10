import sqlite3
import re
from aiogram import Bot
from config import DB_PATH
from aiogram.exceptions import TelegramAPIError

async def check_subscription_status(bot: Bot, user_id: int, channel: str = "") -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT channel_id FROM channels")
        rows = cursor.fetchall()
        channel_ids = [row[0] for row in rows]
    finally:
        conn.close()

    print(f"👤 Foydalanuvchi {user_id} uchun kanallar: {channel_ids}")

    for ch in channel_ids:
        ch_str = str(ch).strip()
        print(f"🔍 Kanal tekshirilmoqda: {ch_str}")

        # 1️⃣ Agar kanal zayavka link bo'lsa (https://t.me/+...)
        # if ch_str.startswith("https://t.me/+"):
            # if not await _check_join_request(user_id, ch_str):
            #     print(f"❌ {user_id} zayavka kanalga qo'shilmagan: {ch_str}")
            #     return True
            # else:
            #     print(f"✅ {user_id} zayavka kanalga qo'shilgan: {ch_str}")
            #     continue

        # 2️⃣ Oddiy kanallarni API orqali tekshirish
        try:
            chat_id = ch_str
            # Agar faqat raqam bo'lsa va -100 bilan boshlanmasa
            if re.match(r"^\d{9,}$", chat_id) and not chat_id.startswith("-100"):
                chat_id = f"-100{chat_id}"

            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                print(f"❌ {user_id} obuna emas: {ch_str}")
                return False
            else:
                print(f"✅ {user_id} kanalga obuna: {ch_str}")

        except TelegramAPIError as e:
            print(f"⚠️ Telegram API xatoligi: {e} — kanal: {ch_str}")
            return True  # API muammosida bloklamaymiz
        except Exception as e:
            print(f"⚠️ Xatolik: {e}")
            return False

    return True


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
        print(f"❌ Database xatosi: {e}")
        return False
    finally:
        conn.close()

    print(f"👤 Foydalanuvchi {user_id} kanal {channel} uchun 'Join' ni tasdiqladi")
    return True
