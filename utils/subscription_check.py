from aiogram import Bot
from config import CHANNEL_IDS

async def check_subscription_status(bot: Bot, user_id: int) -> bool:
    for channel in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True
