from aiogram import Router, F
from aiogram.types import Message

support_router = Router()

@support_router.message(F.text == "/support")
async def support_command(message: Message):
    await message.answer(
        "🆘 <b>Texnik yordam kerakmi?</b>\n\n"
        "Agar sizda savollar, muammolar yoki takliflar bo‘lsa, biz bilan bog‘laning.\n"
        parse_mode="HTML"
    )
