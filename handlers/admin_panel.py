from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.enums import ContentType
from config import ADMIN_IDS, DB_PATH
from utils.gamification import Gamification
from datetime import datetime
import sqlite3
import logging
import asyncio

import sqlite3
from config import DB_PATH
from aiogram import types
from aiogram.fsm.context import FSMContext

admin_router = Router()

class AddMovieForm(StatesGroup):
    code = State()
    title = State()
    genre = State()
    year = State()
    description = State()
    is_premium = State()
    video = State()
    delete = State()

class BlockUserForm(StatesGroup):
    user_id = State()

class BroadcastForm(StatesGroup):
    content = State()
    schedule_time = State()

class AdStates(StatesGroup):
    waiting_for_ad = State()

@admin_router.message(Command("admin"))
async def admin_panel_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 Bu buyruq faqat adminlar uchun!")
        return
    
    logging.info(f"Admin panel accessed by user_id={message.from_user.id}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo‘shish", callback_data="add_movie"),
         InlineKeyboardButton(text="🚫 Foydalanuvchi bloklash", callback_data="block_user")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats"),
         InlineKeyboardButton(text="🎛 Adminlarni boshqarish", callback_data="manage_admins")],
        [InlineKeyboardButton(text="📢 Kanallarni boshqarish", callback_data="manage_channels"),
         InlineKeyboardButton(text="📣 Reklama yuborish", callback_data="send_ad")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilarni boshqarish", callback_data="manage_users"),
         InlineKeyboardButton(text="🎬 Kinolarni boshqarish", callback_data="manage_movies")],
        [InlineKeyboardButton(text="⏰ Reklama rejalashtirish", callback_data="schedule_broadcast")]
    ])
    await message.reply("🎛 Admin paneli:", reply_markup=keyboard)

@admin_router.callback_query(F.data == "add_movie")
async def add_movie_callback(callback: CallbackQuery, state: FSMContext):
    logging.info(f"add_movie callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar kino qo‘shishi mumkin!")
        return
    await state.set_state(AddMovieForm.code)
    await callback.message.reply("🎬 Kino kodi kiriting (masalan, KINO987):")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(AddMovieForm.code)
async def process_movie_code(message: Message, state: FSMContext):
    movie_code = message.text.strip().upper()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT movie_code FROM movies WHERE movie_code = ?", (movie_code,))
    if c.fetchone():
        await message.reply("⚠️ Bu kino kodi allaqachon mavjud!")
        conn.close()
        return
    conn.close()
    await state.update_data(code=movie_code)
    await state.set_state(AddMovieForm.title)
    await message.reply("📽 Kino nomini kiriting:")

@admin_router.message(AddMovieForm.title)
async def process_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieForm.genre)
    await message.reply("🎭 Kino janrini kiriting (masalan, Action):")

@admin_router.message(AddMovieForm.genre)
async def process_movie_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text.strip())
    await state.set_state(AddMovieForm.year)
    await message.reply("📅 Kino yilini kiriting (masalan, 2020):")

@admin_router.message(AddMovieForm.year)
async def process_movie_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.reply("⚠️ Yil raqam bo‘lishi kerak!")
        return
    await state.update_data(year=year)
    await state.set_state(AddMovieForm.description)
    await message.reply("📜 Kino tavsifini kiriting:")

@admin_router.message(AddMovieForm.description)
async def process_movie_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddMovieForm.is_premium)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Premium", callback_data="premium_1"),
         InlineKeyboardButton(text="🆓 Bepul", callback_data="premium_0")]
    ])
    await message.reply("💎 Kino premium bo‘lsinmi?", reply_markup=keyboard)

@admin_router.callback_query(F.data.startswith("premium_"))
async def process_movie_premium(callback: CallbackQuery, state: FSMContext):
    logging.info(f"premium callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    is_premium = int(callback.data.split("_")[1])
    await state.update_data(is_premium=is_premium)
    await state.set_state(AddMovieForm.video)
    await callback.message.reply("🎥 Kino videosini yuboring:")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(AddMovieForm.video, F.content_type == ContentType.VIDEO)
async def process_movie_video(message: Message, state: FSMContext):
    if not message.video:
        await message.reply("⚠️ Iltimos, video yuboring!")
        return
    
    file_id = message.video.file_id
    user_data = await state.get_data()
    movie_code = user_data["code"]
    title = user_data["title"]
    genre = user_data["genre"]
    year = user_data["year"]
    description = user_data["description"]
    is_premium = user_data["is_premium"]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO movies (file_id, movie_code, title, genre, year, description, is_premium) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (file_id, movie_code, title, genre, year, description, is_premium))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "add_movie")
    
    await message.reply(f"🎉 Kino qo‘shildi: {title}\n📊 Yangi XP: {new_xp}")
    await state.clear()

@admin_router.callback_query(F.data == "block_user")
async def block_user_callback(callback: CallbackQuery, state: FSMContext):
    logging.info(f"block_user callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar foydalanuvchilarni bloklashi mumkin!")
        return
    await state.set_state(BlockUserForm.user_id)
    await callback.message.reply("🚫 Bloklash uchun foydalanuvchi ID’sini kiriting:")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(BlockUserForm.user_id)
async def process_block_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.reply("⚠️ Foydalanuvchi ID raqam bo‘lishi kerak!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        await message.reply("⚠️ Bunday foydalanuvchi topilmadi!")
        conn.close()
        return
    
    c.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "block_user")
    
    await message.reply(f"🚫 Foydalanuvchi (ID: {user_id}) bloklandi!\n📊 Yangi XP: {new_xp}")
    await state.clear()

@admin_router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    logging.info(f"stats callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar statistikani ko‘rishi mumkin!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM movies")
    total_movies = c.fetchone()[0]
    c.execute("SELECT SUM(view_count) FROM movies")
    total_views = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM users WHERE subscription_plan IS NOT NULL")
    premium_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
    blocked_users = c.fetchone()[0]
    conn.close()
    
    stats_message = (
        f"📊 Bot statistikasi:\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"🚫 Bloklangan foydalanuvchilar: {blocked_users}\n"
        f"🎬 Kinolar: {total_movies}\n"
        f"👀 Umumiy ko‘rishlar: {total_views}\n"
        f"💎 Premium obunachilar: {premium_users}"
    )
    
    await callback.message.reply(stats_message)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(F.data == "manage_users")
async def manage_users_callback(callback: CallbackQuery):
    logging.info(f"manage_users callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar foydalanuvchilarni boshqarishi mumkin!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Foydalanuvchilar ro‘yxati", callback_data="list_users"),
         InlineKeyboardButton(text="🔓 Foydalanuvchi blokdan chiqarish", callback_data="unblock_user")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
    ])
    await callback.message.reply("👥 Foydalanuvchilarni boshqarish:", reply_markup=keyboard)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(F.data == "list_users")
async def list_users_callback(callback: CallbackQuery):
    logging.info(f"list_users callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar foydalanuvchilarni ko‘rishi mumkin!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, is_blocked, subscription_plan FROM users LIMIT 10")
    users = c.fetchall()
    conn.close()
    
    if not users:
        await callback.message.reply("📭 Foydalanuvchilar topilmadi!")
        return
    
    message_text = "📋 Foydalanuvchilar ro‘yxati:\n\n"
    for user in users:
        status = "🚫 Bloklangan" if user[2] else "✅ Faol"
        subscription = user[3] if user[3] else "🆓 Oddiy"
        message_text += f"ID: {user[0]}\nUsername: @{user[1] or 'N/A'}\nStatus: {status}\nObuna: {subscription}\n\n"
    
    await callback.message.reply(message_text)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(F.data == "unblock_user")
async def unblock_user_callback(callback: CallbackQuery, state: FSMContext):
    logging.info(f"unblock_user callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar foydalanuvchilarni blokdan chiqarishi mumkin!")
        return
    await state.set_state(BlockUserForm.user_id)
    await callback.message.reply("🔓 Blokdan chiqarish uchun foydalanuvchi ID’sini kiriting:")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(BlockUserForm.user_id)
async def process_unblock_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.reply("⚠️ Foydalanuvchi ID raqam bo‘lishi kerak!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ? AND is_blocked = 1", (user_id,))
    if not c.fetchone():
        await message.reply("⚠️ Bunday bloklangan foydalanuvchi topilmadi!")
        conn.close()
        return
    
    c.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "unblock_user")
    
    await message.reply(f"🔓 Foydalanuvchi (ID: {user_id}) blokdan chiqarildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()

@admin_router.callback_query(F.data == "manage_movies")
async def manage_movies_callback(callback: CallbackQuery):
    logging.info(f"manage_movies callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar kinolarni boshqarishi mumkin!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Kinolar ro‘yxati", callback_data="list_movies"),
         InlineKeyboardButton(text="🗑 Kino o‘chirish", callback_data="delete_movie")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
    ])
    await callback.message.reply("🎬 Kinolarni boshqarish:", reply_markup=keyboard)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(F.data == "list_movies")
async def list_movies_callback(callback: CallbackQuery):
    logging.info(f"list_movies callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar kinolarni ko‘rishi mumkin!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT movie_code, title, genre, year, is_premium FROM movies LIMIT 10")
    movies = c.fetchall()
    conn.close()
    
    if not movies:
        await callback.message.reply("📭 Kinolar topilmadi!")
        return
    
    message_text = "🎬 Kinolar ro‘yxati:\n\n"
    for movie in movies:
        premium = "💎 Premium" if movie[4] else "🆓 Bepul"
        message_text += f"Kod: {movie[0]}\nNomi: {movie[1]}\nJanr: {movie[2]}\nYil: {movie[3]}\nStatus: {premium}\n\n"
    
    await callback.message.reply(message_text)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(AddMovieForm.delete)
async def process_delete_code(message: types.Message, state: FSMContext):
    movie_code = message.text.strip()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Avval kino mavjudligini tekshiramiz
        cursor.execute("SELECT * FROM movies WHERE movie_code = ?", (movie_code,))
        movie = cursor.fetchone()

        if not movie:
            await message.reply("❌ Bunday kodga ega kino topilmadi.")
        else:
            cursor.execute("DELETE FROM movies WHERE movie_code = ?", (movie_code,))
            conn.commit()
            await message.reply(f"✅ Kino muvaffaqiyatli o‘chirildi! 🎬\n🎟 Kod: {movie_code}")

    except Exception as e:
        logging.error(f"Error deleting movie: {e}")
        await message.reply("⚠️ O‘chirishda xatolik yuz berdi.")
    finally:
        conn.close()
        await state.clear()

@admin_router.callback_query(F.data == "delete_movie")
async def delete_movie_callback(callback: CallbackQuery, state: FSMContext):
    logging.info(f"delete_movie callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar kinolarni o‘chirishi mumkin!")
        return
    await state.set_state(AddMovieForm.delete)
    await callback.message.reply("🗑 O‘chirish uchun kino kodini kiriting:")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(AddMovieForm.code)
async def process_delete_movie(message: Message, state: FSMContext):
    movie_code = message.text.strip().upper()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT movie_code FROM movies WHERE movie_code = ?", (movie_code,))
    if not c.fetchone():
        await message.reply("⚠️ Bunday kino kodi topilmadi!")
        conn.close()
        return
    
    c.execute("DELETE FROM movies WHERE movie_code = ?", (movie_code,))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "delete_movie")
    
    await message.reply(f"🗑 Kino (Kod: {movie_code}) o‘chirildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()

@admin_router.callback_query(F.data == "schedule_broadcast")
async def schedule_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    logging.info(f"schedule_broadcast callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar reklama rejalashtirishi mumkin!")
        return
    await state.set_state(BroadcastForm.content)
    await callback.message.reply("📣 Rejalashtirilgan reklama matnini kiriting:")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.message(BroadcastForm.content)
async def process_broadcast_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text.strip())
    await state.set_state(BroadcastForm.schedule_time)
    await message.reply("⏰ Yuborish vaqtini kiriting (YYYY-MM-DD HH:MM formatida):")

@admin_router.message(BroadcastForm.schedule_time)
async def process_broadcast_time(message: Message, state: FSMContext):
    try:
        schedule_time = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
        if schedule_time < datetime.now():
            await message.reply("⚠️ Vaqt o‘tmishda bo‘lmasligi kerak!")
            return
    except ValueError:
        await message.reply("⚠️ Noto‘g‘ri vaqt formati! YYYY-MM-DD HH:MM ishlating.")
        return
    
    user_data = await state.get_data()
    ad_content = user_data["content"]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scheduled_broadcasts (content, schedule_time, status) VALUES (?, ?, ?)",
              (ad_content, schedule_time, "pending"))
    conn.commit()
    conn.close()
    
    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "schedule_broadcast")
    
    await message.reply(f"⏰ Reklama {schedule_time} ga rejalashtirildi!\n📊 Yangi XP: {new_xp}")
    await state.clear()

@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin_callback(callback: CallbackQuery):
    logging.info(f"back_to_admin callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    await admin_panel_command(callback.message)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(lambda c: c.data == "send_ad")
async def ask_for_ad(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Faqat adminlar uchun!", show_alert=True)
        return

    await callback.message.answer("📣 Reklama matnini yoki rasm bilan matnni yuboring.")
    await state.set_state(AdStates.waiting_for_ad)

@admin_router.message(AdStates.waiting_for_ad)
async def send_ad_to_users(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 Sizda ruxsat yo'q.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_blocked = 0")
    users = c.fetchall()
    conn.close()

    success_count = 0
    failed_count = 0
    batch_size = 30
    delay = 1

    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        for (user_id,) in batch:
            try:
                if message.photo:
                    await message.bot.send_photo(user_id, photo=message.photo[-1].file_id, caption=message.caption or "")
                else:
                    await message.bot.send_message(user_id, text=message.text)
                success_count += 1
            except Exception as e:
                logging.warning(f"❌ Failed to send ad to user {user_id}: {e}")
                failed_count += 1
        await asyncio.sleep(delay)

    gamification = Gamification()
    new_xp = gamification.add_xp(message.from_user.id, "send_ad")

    await message.answer(
        f"✅ {success_count} ta foydalanuvchiga yuborildi!\n"
        f"❌ Yuborilmadi: {failed_count}\n"
        f"📊 Yangi XP: {new_xp}"
    )

    await state.clear()

@admin_router.callback_query(F.data == "manage_admins")
async def manage_admins_callback(callback: CallbackQuery):
    logging.info(f"manage_admins callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat super adminlar adminlarni boshqarishi mumkin!")
        return
    from handlers.admin.manage_admin import manage_admins_command
    await manage_admins_command(callback.message)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

@admin_router.callback_query(F.data == "manage_channels")
async def manage_channels_callback(callback: CallbackQuery):
    logging.info(f"manage_channels callback triggered by user_id={callback.from_user.id}, callback_data={callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.reply("🚫 Faqat adminlar kanallarni boshqarishi mumkin!")
        return
    from handlers.admin.manage_channel import manage_channels_command
    await manage_channels_command(callback.message)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")