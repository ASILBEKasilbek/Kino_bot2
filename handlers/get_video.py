from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DB_PATH, BOT_TOKEN, CHANNEL_IDS
from database.models import get_movie_by_code, get_all_channels, get_top_movies, add_to_watchlist, set_rating
from utils.subscription_check import check_subscription_status, confirm_join
import sqlite3
from datetime import datetime
import re
import uuid

# State for movie code input
class MovieStates(StatesGroup):
    waiting_for_movie_code = State()

# Router
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
                InlineKeyboardButton(text="🎲 Tasodifiy kino", callback_data="tasodifiy_kinolar"),
            ],
            [
                InlineKeyboardButton(text="📢 Barcha kinolar 📽", url="https://t.me/erotika_kinolar_hikoyalar")
            ]
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

# Helper function to handle movie code
async def _handle_movie_code(message: Message, movie_code: str, bot: Bot):
    movie = get_movie_by_code(movie_code)
    if not movie:
        await message.reply("⚠️ Kino topilmadi!")
        return

    movie_id, file_id, title, genre, year, description, is_premium = movie
    user_id = message.from_user.id

    # Check subscription for premium content
    is_subscribed = await check_subscription_status(bot, user_id, channel="")
    if is_premium and not is_subscribed:
        await message.reply("💎 Bu premium kino! Iltimos, obuna bo‘ling: /buy_subscription")
        return

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

# Start command handler
@video_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    
    # Save user to database
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, registration_date, last_activity) VALUES (?, ?, ?, ?)",
            (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

    # Check subscription status
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    channels = get_all_channels()
    all_joined = True

    for i, channel in enumerate(channels, 1):
        channel_id = str(channel)
        if not channel_id.startswith("-100") and re.match(r"^\d{9,}$", channel_id):
            channel_id = f"-100{channel_id}"
        elif channel_id.startswith("@") or channel_id.startswith("https://t.me/"):
            pass
        else:
            continue

        is_joined = await check_subscription_status(bot, user_id, channel_id)
        if not is_joined:
            all_joined = False
            url = await _get_channel_url(bot, channel_id)
            if url:
                keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"📢 {i} Kanal", url=url)])

    if not all_joined:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subscription")])
        await message.reply(
            f"👋 Xush kelibsiz, {username}!\n"
            f"🎬 Kino olish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return

    # Handle movie code from /start command
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        await _handle_movie_code(message, args[1].strip().upper(), bot)
        return

    # Show main menu
    await _show_main_menu(message, username, state)

# Handle movie code input
@video_router.message(MovieStates.waiting_for_movie_code)
async def handle_movie_code(message: Message, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    await _handle_movie_code(message, message.text.strip().upper(), bot)

# Handle get video callback
@video_router.callback_query(F.data == "get_video")
async def process_get_video_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎬 Iltimos, kino kodini yuboring. Masalan: `123`", parse_mode="Markdown")
    await state.set_state(MovieStates.waiting_for_movie_code)
    await callback.answer()

# Handle subscription check
@video_router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery, state: FSMContext):
    bot = Bot(token=BOT_TOKEN)
    user_id = callback.from_user.id
    is_subscribed = await check_subscription_status(bot, user_id, channel="")
    username = callback.from_user.username or "No username"

    if is_subscribed:
        await _show_main_menu(callback.message, username, state)
    else:
        await callback.answer("❌ Siz hali ham obuna emassiz!", show_alert=True)

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
    c.execute("SELECT id, title FROM movies ORDER BY RANDOM() LIMIT 1")
    movie = c.fetchone()
    conn.close()

    if not movie:
        await callback.message.answer("❌ Kino topilmadi.")
        return

    buttons = [[InlineKeyboardButton(text=movie[1], callback_data=f"movie_{movie[0]}")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🎲 Tasodifiy kino:", reply_markup=keyboard)
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

# MarkdownV2 belgilarini qochirish uchun funksiya
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
            f"➡ Tomosha qilish uchun pastdagi tugmani bosing 👇"
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

# Helper function for movie buttons
def movie_buttons(movie_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
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