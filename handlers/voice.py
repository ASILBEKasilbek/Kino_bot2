from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.gamification import Gamification
from handlers.video import search_movie_command
from handlers.get_video import get_video_command
import speech_recognition as sr
import os

voice_router = Router()

class VoiceForm(StatesGroup):
    command = State()

@voice_router.message(F.content_type == ContentType.VOICE)
async def process_voice_command(message: Message, state: FSMContext):
    path = f"uploads/voice_{message.from_user.id}.ogg"
    voice_file = await message.bot.download(message.voice.file_id, destination=path)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(voice_file.name) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="uz-UZ").lower()

        os.remove(voice_file.name)

        if "kino top" in text or "film qidir" in text:
            query = text.replace("kino top", "").replace("film qidir", "").strip()
            if query:
                await message.answer(f"🔍 '{query}' bo‘yicha qidirilmoqda...")
                await search_movie_command(message.__class__(text=f"/search_movie {query}", **message.__dict__))
            else:
                await message.answer("⚠️ Qidiruv so‘zini aniq ayting!")
        elif "kino ol" in text or "film yubor" in text:
            code = text.replace("kino ol", "").replace("film yubor", "").strip().upper()
            if code:
                await message.answer(f"🎬 '{code}' kodli kino olinmoqda...")
                await get_video_command(message.__class__(text=f"/get_video {code}", **message.__dict__))
            else:
                await message.answer("⚠️ Kino kodini aniq ayting!")
        elif "tavsiya" in text:
            await message.answer("🎬 Tavsiya so‘ralmoqda...")
            from core.ai_recommendation import recommend_command
            await recommend_command(message.__class__(text="/recommend", **message.__dict__))
        else:
            await message.answer("⚠️ Tushunilmadi! Iltimos, 'kino top', 'kino ol' yoki 'tavsiya' deb ayting.")

        gamification = Gamification()
        new_xp = gamification.add_xp(message.from_user.id, "voice_command")
        await message.answer(f"📊 Yangi XP: {new_xp}")

    except sr.UnknownValueError:
        await message.answer("⚠️ Ovozli xabarni aniqlab bo‘lmadi!")
    except sr.RequestError:
        await message.answer("⚠️ Ovozli xabarni qayta ishlashda xatolik!")
    finally:
        if os.path.exists(voice_file.name):
            os.remove(voice_file.name)

    await state.clear()
