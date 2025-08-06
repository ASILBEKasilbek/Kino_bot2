from aiogram import Router, F
from aiogram.types import Message,CallbackQuery
from config import DB_PATH,BOT_TOKEN,CHANNEL_IDS,CHANNEL_ID
from database.models import get_movie_by_code
from utils.subscription_check import check_subscription_status,confirm_join
from aiogram import Bot
import sqlite3
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.models import get_top_movies,get_all_channels
import re
import sqlite3
import uuid
from aiogram import types
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
class MovieStates(StatesGroup):
    waiting_for_movie_code = State()
video_router = Router()


@video_router.callback_query(F.data == "get_video")
async def process_get_video_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎬 Iltimos, kino kodini yuboring. Masalan: `123`", parse_mode="Markdown")
    await state.set_state(MovieStates.waiting_for_movie_code)
    await callback.answer()


@video_router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery, bot: Bot ,state: FSMContext):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription_status(bot, user_id,channel="")

    username = callback.message.from_user.username or "No username"

    if is_subscribed:
        
    # Agar startda kod bo'lmasa - oddiy menyu chiqar
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔎 Qidiruv", switch_inline_query_current_chat=""),
                InlineKeyboardButton(text="Top 5 kinolar", callback_data="top_5_kinolar")],
                [InlineKeyboardButton(text="📢 Barcha kinolar", url="https://t.me/kino_kodlar_t")]
            ]
        )
        await callback.message.edit_text(
            f"🎬 <b>Sekret KinoBot</b> ga xush kelibsiz, <b>{username}</b>!\n\n"
            "📽 Bu yerda siz sirli va noyob kinolarni topasiz — qidiruv, tavsiyalar, maxsus to‘plamlar va boshqa ko‘plab imkoniyatlar sizni kutmoqda!\n\n"
            "🧾 <i>Iltimos, kino kodini yuboring yoki quyidagi menyudan birini tanlang:</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await state.set_state(MovieStates.waiting_for_movie_code)
    else:
        await callback.answer("❌ Siz hali ham obuna emassiz!", show_alert=True)

@video_router.callback_query(F.data.startswith("join_"))
async def handle_join_click(callback: CallbackQuery, bot: Bot):
    channel_id = callback.data.split("join_")[1]
    user_id = callback.from_user.id
    print(f"Foydalanuvchi {user_id} kanal {channel_id} ga join bosdi")

    success = await confirm_join(bot, user_id, channel_id)
    if success:
        await callback.answer("✅ Join bosilgan deb qayd etildi", show_alert=True)
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

@video_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    print(message)
    bot = Bot(token=BOT_TOKEN)
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registration_date, last_activity) VALUES (?, ?, ?, ?)",
              (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    channels = get_all_channels()
    all_joined = True
    user_id = message.from_user.id  # foydalanuvchining ID
    i = 1

    print("Kanallar:", channels)

    for channel in channels:
        url = ""
        print(f"Channel: {channel}")

        # Kanal ID ni aniqlash
        if isinstance(channel, int):
            channel_id = f"-100{channel}" if not str(channel).startswith("-100") else str(channel)
        elif re.match(r"^\d{9,}$", str(channel)):
            channel_id = f"-100{channel}" if not str(channel).startswith("-100") else str(channel)
        else:
            channel_id = channel

        # Foydalanuvchi shu kanal uchun join bosganmi yoki yo'q
        is_joined = await check_subscription_status(bot, user_id, channel_id)
        if not is_joined:
            all_joined = False

            # URL yaratish
            if str(channel_id).startswith('@'):
                url = f"https://t.me/{channel_id.lstrip('@')}"
            elif str(channel_id).startswith("https://t.me/"):
                url = channel_id
            elif re.match(r"^-100\d+$", str(channel_id)):
                try:
                    chat = await bot.get_chat(channel_id)
                    if chat.username:
                        url = f"https://t.me/{chat.username}"
                    else:
                        url = f"https://t.me/c/{channel_id.lstrip('-100')}/1"
                except Exception as e:
                    print(f"Xatolik chatni olishda: {e}")
                    continue
            else:
                continue  # Tushunarsiz format bo‘lsa

            # Kanal tugmasi
            button = InlineKeyboardButton(
                text=f"📢 {i} Kanal",
                url=url
            )
            keyboard.inline_keyboard.append([button])
            i += 1

    # Agar kamida 1 ta kanalga join bosilmagan bo‘lsa
    if not all_joined:
        # "Obuna bo‘ldim" tugmasi
        check_button = InlineKeyboardButton(
            text="✅ Obuna bo‘ldim",
            callback_data="check_subscription"
        )
        keyboard.inline_keyboard.append([check_button])

        await message.reply(
            f"👋 Xush kelibsiz, {username}!\n"
            f"🎬 Kino olish uchun quyidagi kanallarga obuna bo‘ling yoki join tugmasini bosing:",
            reply_markup=keyboard
        )
        return


        
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        movie_code = args[1].strip().upper()
        movie = get_movie_by_code(movie_code)

        if movie:
            movie_id, file_id, title, genre, year, description, is_premium = movie

            if is_premium and not all_joined:
                await message.reply("💎 Bu premium kino! Iltimos, obuna bo‘ling: /buy_subscription")
                return

            # Statistikani yangilash
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE movies SET view_count = view_count + 1 WHERE id = ?", (movie_id,))
            c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?",
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
            conn.commit()
            conn.close()

            caption = (
                f"🎬 <b>{title}</b> ({year})\n"
                f"🎭 <b>Janr:</b> {genre}\n"
                f"📝 <b>Tavsif:</b>\n{description}\n\n"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Barcha kinolar", url="https://t.me/erotika_kinolar_hikoyalar")],
                ]
            )
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
                protect_content=True
            )
            return
        else:
            await message.reply("⚠️ Kino kodi noto‘g‘ri yoki mavjud emas.")
            return

    # Agar startda kod bo'lmasa - oddiy menyu chiqar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Qidiruv", switch_inline_query_current_chat=""),
             InlineKeyboardButton(text="Top 5 kinolar", callback_data="top_5_kinolar")],
            [InlineKeyboardButton(text="📢 Barcha kinolar", url="https://t.me/erotika_kinolar_hikoyalar")]
        ]
    )
    await message.answer(
        f"🎬 <b>Sekret KinoBot</b> ga xush kelibsiz, <b>{username}</b>!\n\n"
        "📽 Bu yerda siz sirli va noyob kinolarni topasiz — qidiruv, tavsiyalar, maxsus to‘plamlar va boshqa ko‘plab imkoniyatlar sizni kutmoqda!\n\n"
        "🧾 <i>Iltimos, kino kodini yuboring yoki quyidagi menyudan birini tanlang:</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await state.set_state(MovieStates.waiting_for_movie_code)
    print(90)

@video_router.message(MovieStates.waiting_for_movie_code)
async def handle_movie_code(message: Message, state: FSMContext):
    movie_code = message.text.strip().upper()
    print(movie_code)
    movie = get_movie_by_code(movie_code)
    print(message.text)
    
    if not movie:
        await message.reply("⚠️ Kino topilmadi!")
        return
    print(movie)
    movie_id, file_id, title, genre, year, description, is_premium = movie
    print(f"Movie ID: {movie_id}, File ID: {file_id}, Title: {title}, Genre: {genre}, Year: {year}, Description: {description}, Is Premium: {is_premium}")
    
    
    bot = Bot(token=BOT_TOKEN)
    # is_subscribed = await check_subscription_status(bot, message.from_user.id)

    # if is_premium and not is_subscribed:
    #     await message.reply("💎 Bu premium kino! Iltimos, obuna bo‘ling: /buy_subscription")
    #     return
    
    conn = sqlite3.connect(DB_PATH)
    print(92)
    c = conn.cursor()
    c.execute("UPDATE movies SET view_count = view_count + 1 WHERE id = ?", (movie_id,))
    c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    conn.close()
    caption = (
        f"🎬 <b>{title}</b> ({year})\n"
        f"🎭 <b>Janr:</b> {genre}\n"
        f"📝 <b>Tavsif:</b>\n{description}\n\n"
    )
    print(93)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Barcha kodlar",url="https://t.me/erotika_kinolar_hikoyalar")
            ]
        ]
    )
    print(94)
    await bot.send_video(
        chat_id=message.chat.id,
        video=file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard,
        protect_content=True  # Video faylni himoya qilish
    )

    # await state.clear()

@video_router.callback_query(lambda c: c.data == "top_5_kinolar")
async def top_5_handler(callback: CallbackQuery):
    top_movies = get_top_movies(5)
    buttons = []
    for movie in top_movies:
        buttons.append([
            InlineKeyboardButton(
                text=movie['title'],  # tugmada kino nomi
                callback_data=f"movie_{movie['id']}"  # callback_data orqali kino ID yuboramiz
            )
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer("🎬 Top 5 kinolar:", reply_markup=keyboard)
    await callback.answer()

@video_router.callback_query(lambda c: c.data.startswith("movie_"))
async def send_selected_movie(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])  # movie_3 -> 3
    top_movies = get_top_movies(100)  # Yoki boshqa funksiya bilan ID bo‘yicha kino ol
    movie = next((m for m in top_movies if m["id"] == movie_id), None)

    if movie:
        await callback.message.answer_video(
            video=movie['file_id'],
            caption=f"{movie['title']} ({movie['year']})\nJanr: {movie['genre']} \nTavsif: {movie['description']}",
        )
    else:
        await callback.message.answer("Kechirasiz, kino topilmadi.")

    await callback.answer()


@video_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    
    query = inline_query.query.strip()

    results = []
    conn = sqlite3.connect('database/bot.db')
    c = conn.cursor()

    if query:
        c.execute("SELECT * FROM movies WHERE title LIKE ? OR description LIKE ? LIMIT 20", (f"%{query}%", f"%{query}%"))
    else:
        c.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 20")
    
    movies = c.fetchall()

    if movies:
        for movie in movies:
            movie_id = movie[0]
            file_id = movie[1]
            movie_code = movie[2]
            title = movie[3]
            genre = movie[4]
            year = movie[5]
            description = movie[6]
            is_premium = movie[7]
            view_count = movie[8]
            a='Sekret_kinoborbot'
            a1 = "Healthy_Helper_robot"
            btn = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🎬 Tomosha qilish",
                            url=f"https://t.me/{a}?start={movie_code}"
                        )
                    ]
                ]
            )
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{title} ({year})",
                    description=f"{genre} • {year}",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"*🎬 {title}*\n"
                            f"📅 *Yil:* {year}\n"
                            f"🎭 *Janr:* {genre}\n"
                            f"📝 *Tavsif:* {description}\n"
                            f"👁 *Ko'rilgan:* {view_count} marta\n\n"
                            f"➡ Tomosha qilish uchun pastdagi tugmani bosing 👇"
                        ),
                        parse_mode="Markdown"
                    ),
                    reply_markup=btn,
                )
            )
    else:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Hech narsa topilmadi",
                input_message_content=InputTextMessageContent(
                    message_text="Kechirasiz, siz so‘ragan film topilmadi."
                )
            )
        )

    await inline_query.answer(results, cache_time=1)
    conn.close()

@video_router.callback_query(lambda c: c.data == "barcha_kinolar")
async def show_all_movies(callback_query: CallbackQuery):
    conn = sqlite3.connect('database/bot.db')
    c = conn.cursor()
    c.execute("SELECT title, movie_code FROM movies")
    movies = c.fetchall()
    conn.close()

    if not movies:
        await callback_query.message.answer("📭 Bazada hech qanday kino yo'q.")
        return

    buttons = []
    for title, code in movies:
        buttons.append(
            [InlineKeyboardButton(text=title, url=f"https://t.me/Sekret_kinoborbot?start={code}")]
        )

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.answer("🎬 Barcha kinolar:", reply_markup=markup)
    await callback_query.answer()  # ✅ Callback tugmasiga javob berishni unutmang