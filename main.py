import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.get_video import video_router
from handlers.support import support_router
from handlers.daily_reminder import reminder_router, setup_scheduler
from handlers.admin_panel import admin_router
from handlers.admin.manage_admin import admin_manage_router
from handlers.admin.manage_channel import channel_manage_router
from handlers.admin.send_ads import ad_router
from database.db import init_db
from utils.logger import Logger
from aiogram import types
ADMIN_IDS = [5306481482,7646223205,5902572920,1846386540,5705506626,7549237020,8297316764]
ADMIN_IDS = [5306481482, 7646223205, 5902572920, 1846386540, 5705506626, 7549237020, 8297316764]

async def set_default_commands(bot: Bot):
    # Oddiy foydalanuvchilar uchun komandalar
    user_commands = [
        types.BotCommand(command="start", description="⚪️ Botni ishga tushirish"),
        types.BotCommand(command="admin", description="🎛 Admin paneli"),
    ]

    # Adminlar uchun komandalar
    admin_commands = user_commands + [
        types.BotCommand(command="k", description="🎬 Kino qo‘shish"),
    ]

    # Har bir admin uchun alohida o‘rnatiladi
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope=types.BotCommandScopeChat(chat_id=admin_id))
            print(f"✅ Admin komandalar o‘rnatildi: {admin_id}")
        except Exception as e:
            print(f"❌ Admin {admin_id} uchun komandalar o‘rnatilmadi: {e}")

    # Qolgan barcha foydalanuvchilar uchun umumiy komandalar
    await bot.set_my_commands(user_commands)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(support_router)
    dp.include_router(admin_router)
    dp.include_router(video_router)
    dp.include_router(admin_manage_router)
    dp.include_router(channel_manage_router)
    
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
