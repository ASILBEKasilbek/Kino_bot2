from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DB_PATH, BOT_TOKEN, CHANNEL_IDS,ADMIN_IDS
from database.models import get_movie_by_code, get_all_channels, get_top_movies, add_to_watchlist, set_rating
# from utils.subscription_check import check_subscription_status, confirm_join
import sqlite3
from datetime import datetime
import re
import uuid
from .buttons import movie_buttons
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import ChatJoinRequest
# State for movie code input
class MovieStates(StatesGroup):
    waiting_for_movie_code = State()


video_router = Router()

# Helper function to get channel URL
async def _get_channel_url(bot: Bot, channel_id: str) -> str:
    try:
        if channel_id.startswith("@"):
            return f"https://t.me/{channel_id.lstrip('@')}"
        elif channel_id.startswith("https://t.me/"):
            return channel_id
        elif re.match(r"^-100\d+$", channel_id):
            chat = await bot.get_chat(channel_id)
            return f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{channel_id.lstrip('-100')}/1"
    except Exception as e:
        print(f"Error getting channel URL: {e}")
    return ""

# Helper function to show main menu
async def _show_main_menu(message: Message, username: str, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Qidirish", switch_inline_query_current_chat=""),
                InlineKeyboardButton(text="🎯 Top 5 kinolar", callback_data="top_5_kinolar")
            ],
            [
                InlineKeyboardButton(text="🎬 Bugungi tavsiya", callback_data="kunlik_film_tavsiyasi"),
                InlineKeyboardButton(text="🏆 Haftaning eng zo‘ri", callback_data="haftalik_film_tavsiyasi"),
            ],
            [
                InlineKeyboardButton(text="🌟 Oyning TOP filmi", callback_data="oylik_film_tavsiyasi"),
                InlineKeyboardButton(text="🎲 Tasodifiy 7 kino", callback_data="tasodifiy_kinolar"),
            ],
            [
                InlineKeyboardButton(text="📢 Barcha kinolar 📽", url="https://t.me/erotika_kinolar_hikoyalar")
            ]
        ]
    )

    await message.answer(
        f"🎬 <b>Sekret KinoBot</b>ga xush kelibsiz, <b>{username}</b>!\n\n"
        "📽 Bu yerda siz sirli va noyob kinolarni topasiz — qidiruv, tavsiyalar, maxsus to‘plamlar va boshqa ko‘plab imkoniyatlar sizni kutmoqda!\n\n"
        "🧾 <i>Iltimos, kino kodini yuboring yoki quyidagi menyudan birini tanlang:</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(MovieStates.waiting_for_movie_code)

# from aiogram import F

# @video_router.message()  # Har qanday xabar
# async def check_channels_before_any_message(message: Message, state: FSMContext):
#     bot = Bot(token=BOT_TOKEN)
#     user_id = message.from_user.id
#     username = message.from_user.username or "No username"
#     if user_id in ADMIN_IDS:
#         return 
#     channels = get_all_channels()  # [(channel_id, channel_link), ...]
#     all_joined = True
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[])

#     for i, (channel_id, channel_link) in enumerate(channels, 1):
#         if re.match(r"^\d{9,}$", channel_id) and not channel_id.startswith("-100"):
#             channel_id = f"-100{channel_id}"

#         is_joined = await check_subscription_status(bot, user_id, channel_id)
#         if not is_joined:
#             all_joined = False
#             keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"📢 {i} Kanal", url=channel_link)])

#     if not all_joined:
#         keyboard.inline_keyboard.append(
#             [InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subscription")]
#         )
#         await message.reply(
#             "❌ Avval quyidagi kanallarga obuna bo‘ling:",
#             reply_markup=keyboard
#         )
#         return  # bu yerda boshqa handlerlar ishlamaydi

#     current_state = await state.get_state()
#     if current_state == MovieStates.waiting_for_movie_code.state:
#         if message.text=='/start':
#             await _show_main_menu(message, username, state)
#             return
#         await _handle_movie_code(message, message.text.strip().upper(), bot)
#     else:
#         await _show_main_menu(message, username, state)

async def _handle_movie_code(message: Message, movie_code: str, bot: Bot):
    text = (message.text or "").strip()
    match = re.search(r"KOD:\s*(\w+)", text)
    if match:
        kod = match.group(1)
    movie = get_movie_by_code(movie_code)
    if movie==None:
        await message.reply("⚠️ Kino topilmadi!")
        return 
    if not movie:
        movie = get_movie_by_code(movie_code)
        if not movie:
            await message.reply("⚠️ Kino topilmadi!")
            return

    movie_id, file_id, title, genre, year, description, is_premium = movie
    user_id = message.from_user.id

    # Check subscription for premium content
    # is_subscribed = await check_subscription_status(bot, user_id, channel="")
    # if is_premium and not is_subscribed:
    #     await message.reply("💎 Bu premium kino! Iltimos, obuna bo‘ling: /buy_subscription")
    #     return

    # Update statistics
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE movies SET view_count = view_count + 1 WHERE id = ?", (movie_id,))
        c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()

    caption = f"🎬 <b>{title}</b> ({year})\n🎭 <b>Janr:</b> {genre}\n📝 <b>Tavsif:</b>\n{description}\n\n"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Barcha kodlar", url="https://t.me/erotika_kinolar_hikoyalar")],
            [InlineKeyboardButton(text="➕ Watchlist", callback_data=f"watchlist_add_{movie_id}")],
            [
                InlineKeyboardButton(text="⭐1", callback_data=f"rate_{movie_id}_1"),
                InlineKeyboardButton(text="⭐2", callback_data=f"rate_{movie_id}_2"),
                InlineKeyboardButton(text="⭐3", callback_data=f"rate_{movie_id}_3"),
                InlineKeyboardButton(text="⭐4", callback_data=f"rate_{movie_id}_4"),
                InlineKeyboardButton(text="⭐5", callback_data=f"rate_{movie_id}_5"),
            ]
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


@video_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, registration_date, last_activity) VALUES (?, ?, ?, ?)",
            (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    channels = get_all_channels()  # hozir [(channel_id, channel_link), ...] qaytadi
    all_joined = True
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i, (channel_id, channel_link) in enumerate(channels, 1):

        if re.match(r"^\d{9,}$", channel_id) and not channel_id.startswith("-100"):
            channel_id = f"-100{channel_id}"

        is_joined = await check_subscription_status(bot, user_id, channel_id)
        if not is_joined:
            all_joined = False
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"📢 {i} Kanal", url=channel_link)])

    if not all_joined:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subscription")]
        )
        await message.reply(
            "❌ Avval quyidagi kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return
    await _show_main_menu(message, username, state)

pending_requests = {}  

async def check_subscription_status(bot: Bot, user_id: int, channel_id: str) -> bool:
    try:
        chat_id = str(channel_id).strip()

        # Kanal ID formatlash (-100 bilan bo‘lmasa qo‘shamiz)
        if re.match(r"^\d{9,}$", chat_id) and not chat_id.startswith("-100"):
            chat_id = f"-100{chat_id}"
        # 1️⃣ Avval pending request bor-yo‘qligini tekshiramiz
        if user_id in pending_requests and chat_id in pending_requests[user_id]:
            return True

        # 2️⃣ Agar yo‘q bo‘lsa oddiy a’zolikni tekshiramiz
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest:
        return False
    except TelegramAPIError:
        return False
    except Exception:
        return False


# Join request handler
@video_router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest):
    user_id = event.from_user.id
    channel_id = str(event.chat.id)

    # Dict ichiga yozamiz 
    if user_id not in pending_requests:
        pending_requests[user_id] = []
    pending_requests[user_id].append(channel_id)

# Handle subscription check
@video_router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    user_id = callback.from_user.id
    username = callback.from_user.username or "No username"

    channels = get_all_channels()  # [(channel_id, channel_link), ...]
    all_joined = True

    for channel_id, _ in channels:
        # Kanal ID formatlash
        if re.match(r"^\d{9,}$", channel_id) and not channel_id.startswith("-100"):
            channel_id = f"-100{channel_id}"

        is_joined = await check_subscription_status(bot, user_id, channel_id)
        if not is_joined:
            all_joined = False
            break

    if all_joined:
        await _show_main_menu(callback.message, username, state)
    else:
        await callback.answer("❌ Siz hali ham barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)

@video_router.message(MovieStates.waiting_for_movie_code)
async def handle_movie_code(message: Message, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    user_id = message.from_user.id
    username = message.from_user.username or "No username"

    channels = get_all_channels()  # [(channel_id, channel_link), ...]
    all_joined = True
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i, (channel_id, channel_link) in enumerate(channels, 1):
        if re.match(r"^\d{9,}$", channel_id) and not channel_id.startswith("-100"):
            channel_id = f"-100{channel_id}"

        is_joined = await check_subscription_status(bot, user_id, channel_id)
        if not is_joined:
            all_joined = False
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"📢 {i} Kanal", url=channel_link)])

    if not all_joined:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subscription")]
        )
        await message.reply(
            "❌ Avval quyidagi kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return
    if message.text=='/start':
        await _show_main_menu(message, username, state)
        return
    await _handle_movie_code(message, message.text.strip().upper(), bot)

# Handle join click
@video_router.callback_query(F.data.startswith("join_"))
async def handle_join_click(callback: CallbackQuery):
    bot = Bot(token=BOT_TOKEN)
    channel_id = callback.data.split("join_")[1]
    success = await confirm_join(bot, callback.from_user.id, channel_id)
    await callback.answer(
        "✅ Join bosilgan deb qayd etildi" if success else "❌ Xatolik yuz berdi",
        show_alert=True
    )



# 📌 Top 5 kinolar
@video_router.callback_query(F.data == "top_5_kinolar")
async def top_5_handler(callback: CallbackQuery):
    top_movies = get_top_movies(5)
    if not top_movies:
        await callback.message.answer("❌ Hozircha top kinolar yo‘q.")
        return

    buttons = [
        [InlineKeyboardButton(text=f"{i+1}. {movie['title']}", callback_data=f"movie_{movie['id']}")]
        for i, movie in enumerate(top_movies)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🎯 Top 5 kinolar:", reply_markup=keyboard)
    await callback.answer()

# 📌 Bugungi tavsiya
@video_router.callback_query(F.data == "kunlik_film_tavsiyasi")
async def daily_movie(callback: CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title FROM movies ORDER BY RANDOM() LIMIT 1")
    movie = c.fetchone()
    conn.close()

    if not movie:
        await callback.message.answer("❌ Kino topilmadi.")
        return

    buttons = [[InlineKeyboardButton(text=movie[1], callback_data=f"movie_{movie[0]}")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🎬 Bugungi tavsiya:", reply_markup=keyboard)
    await callback.answer()

# 📌 Haftaning eng zo‘ri
@video_router.callback_query(F.data == "haftalik_film_tavsiyasi")
async def weekly_best(callback: CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title FROM movies ORDER BY view_count DESC LIMIT 1")
    movie = c.fetchone()
    conn.close()

    if not movie:
        await callback.message.answer("❌ Kino topilmadi.")
        return

    buttons = [[InlineKeyboardButton(text=movie[1], callback_data=f"movie_{movie[0]}")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🏆 Haftaning eng zo‘ri:", reply_markup=keyboard)
    await callback.answer()


# 📌 Oyning TOP filmi
@video_router.callback_query(F.data == "oylik_film_tavsiyasi")
async def monthly_best(callback: CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title FROM movies ORDER BY view_count DESC LIMIT 1")
    movie = c.fetchone()
    conn.close()

    if not movie:
        await callback.message.answer("❌ Kino topilmadi.")
        return

    buttons = [[InlineKeyboardButton(text=movie[1], callback_data=f"movie_{movie[0]}")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🌟 Oyning TOP filmi:", reply_markup=keyboard)
    await callback.answer()


# 📌 Tasodifiy kino
@video_router.callback_query(F.data == "tasodifiy_kinolar")
async def random_movie(callback: CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title FROM movies ORDER BY RANDOM() LIMIT 7")
    movies = c.fetchall()
    conn.close()

    if not movies:
        await callback.message.answer("❌ Kino topilmadi.")
        return

    # 7 ta kino tugmasini yaratish
    buttons = [
        [InlineKeyboardButton(text=f"{i+1}. {movie[1]}", callback_data=f"movie_{movie[0]}")]
        for i, movie in enumerate(movies)
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🎲 Tasodifiy 7 ta kino:", reply_markup=keyboard)
    await callback.answer()


# Handle selected movie
@video_router.callback_query(F.data.startswith("movie_"))
async def send_selected_movie(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    top_movies = get_top_movies(100)
    movie = next((m for m in top_movies if m["id"] == movie_id), None)

    if movie:
        keyboard = movie_buttons(movie['id'])
        await callback.message.answer_video(
            video=movie['file_id'],
            caption=f"{movie['title']} ({movie['year']})\nJanr: {movie['genre']} \nTavsif: {movie['description']}",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer("Kechirasiz, kino topilmadi.")
    await callback.answer()

def escape_md(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    for ch in escape_chars:
        text = text.replace(ch, f"\\{ch}")
    return text

@video_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    results = []

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        if query:
            c.execute(
                "SELECT * FROM movies WHERE title LIKE ? OR description LIKE ? LIMIT 20",
                (f"%{query}%", f"%{query}%")
            )
        else:
            c.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 20")
        movies = c.fetchall()

    for movie in movies:
        movie_id, file_id, movie_code, title, genre, year, description, is_premium, view_count = movie

        btn = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎬 Tomosha qilish",
                        url=f"https://t.me/Sekret_kinoborbot?start={movie_code}"
                    )
                ]
            ]
        )

        # Belgilarni qochirish
        safe_title = escape_md(str(title))
        safe_genre = escape_md(str(genre))
        safe_description = escape_md(str(description))
        safe_year = escape_md(str(year))
        safe_views = escape_md(str(view_count))

        message_text = (
            f"*🎬 {safe_title}*\n"
            f"📅 *Yil:* {safe_year}\n"
            f"🎭 *Janr:* {safe_genre}\n"
            f"📝 *Tavsif:* {safe_description}\n"
            f"👁 *Ko'rilgan:* {safe_views} marta\n\n"
            f"➡ Tomosha qilish uchun pastdagi tugmaniclear bosing 👇\n"
            f"🎟 KOD: {movie_code}"
        )

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"{title} ({year})",
                description=f"{genre} • {year}",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="MarkdownV2"
                ),
                reply_markup=btn
            )
        )

    if not results:
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

# Handle watchlist
@video_router.callback_query(F.data.startswith("watchlist_add_"))
async def handle_watchlist(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[2])
    success = add_to_watchlist(callback.from_user.id, movie_id)
    await callback.answer(
        "🎬 Watchlist-ga qo‘shildi!" if success else "✅ Allaqachon ro‘yxatda!",
        show_alert=True
    )

# Handle rating
@video_router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    _, movie_id, rating = callback.data.split("_")
    set_rating(callback.from_user.id, int(movie_id), int(rating))
    await callback.answer(f"⭐ {rating} baho berildi!", show_alert=True)

# Show all movies
@video_router.callback_query(F.data == "barcha_kinolar")
async def show_all_movies(callback_query: CallbackQuery):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT title, movie_code FROM movies")
        movies = c.fetchall()

    if not movies:
        await callback_query.message.answer("📭 Bazada hech qanday kino yo'q.")
        return

    buttons = [[InlineKeyboardButton(text=title, url=f"https://t.me/Sekret_kinoborbot?start={code}")] for title, code in movies]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("🎬 Barcha kinolar:", reply_markup=markup)
    await callback_query.answer()