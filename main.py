import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.start import start_router
from handlers.get_video import video_router
from handlers.subscription import subscription_router
from handlers.video import search_router
from handlers.feedback import feedback_router
from handlers.referral import referral_router
from handlers.playlist import playlist_router
from handlers.advertising import advertising_router
from handlers.upcoming import upcoming_router
from handlers.support import support_router
# from handlers.voice import voice_router
from handlers.daily_reminder import reminder_router, setup_scheduler
from handlers.admin_panel import admin_router
from handlers.admin.manage_admin import admin_manage_router
from handlers.admin.manage_channel import channel_manage_router
from handlers.admin.send_ads import ad_router
from database.db import init_db
from utils.logger import Logger
from marketing.landing_page import landing_page_router
from aiogram import types

async def set_default_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="⚪️ Botni ishga tushirish"),
        #types.BotCommand(command="get_video", description="🎬 Kino kodini yuborish"),
        types.BotCommand(command="support", description="🆘 Texnik yordam"),
    ]
    
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    print("Bot ishga tushmoqda...")

    dp.include_router(support_router)
    dp.include_router(admin_router)
    dp.include_router(admin_manage_router)
    dp.include_router(channel_manage_router)
    dp.include_router(start_router)
    dp.include_router(video_router)
    # dp.include_router(subscription_router)
    # dp.include_router(search_router)
    # dp.include_router(feedback_router)
    # dp.include_router(referral_router)
    # dp.include_router(playlist_router)
    # dp.include_router(advertising_router)
    # dp.include_router(upcoming_router)
    # dp.include_router(voice_router)
    # dp.include_router(reminder_router)
    # dp.include_router(ad_router)
    # dp.include_router(landing_page_router)
    
    init_db()
    await set_default_commands(bot)
    setup_scheduler()
    
    logger = Logger()
    logger.info("Bot ishga tushdi")
    print("Bot ishga tushdi")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Botda xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
