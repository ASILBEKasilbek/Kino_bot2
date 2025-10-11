import sqlite3
import re
from aiogram import Bot
from config import DB_PATH
from aiogram.exceptions import TelegramAPIError
import re
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

async def check_subscription_status(bot: Bot, user_id: int, channel_id: str) -> bool:
    print(90)
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