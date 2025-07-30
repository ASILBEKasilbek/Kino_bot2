from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from config import CHANNEL_IDS

async def check_subscription_status(bot: Bot, user_id: int) -> bool:
    for channel in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                print(f"❌ Foydalanuvchi {user_id} {channel} kanalida obuna emas: {member.status}")
                return False
        except TelegramAPIError as e:
            print(f"❌ Telegram API xatoligi: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Boshqa xatolik: {e}")
            return False
    return True
