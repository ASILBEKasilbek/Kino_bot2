from aiogram import Router, F
from aiogram.types import Message

support_router = Router()

@support_router.message(F.text == "/support")
async def support_command(message: Message):
    await message.answer(
        "🆘 <b>Texnik yordam kerakmi?</b>\n\n"
        "Agar sizda savollar, muammolar yoki takliflar bo‘lsa, biz bilan bog‘laning.\n"
        "📢 <a href='https://t.me/Dasturch1_asilbek'>Texnik yordam kanali</a> orqali 24/7 xizmatdamiz.",
        parse_mode="HTML"
    )
