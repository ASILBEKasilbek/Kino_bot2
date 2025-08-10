from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN =os.getenv("BOT_TOKEN")  # Telegram bot tokeni
ADMIN_IDS = [5306481482,7646223205,5902572920,1846386540,5705506626,7549237020]  # Admin foydalanuvchi ID’lari
# CHANNEL_IDS = ['2052256946']5306481482
#  # Majburiy obuna kanallari
CHANNEL_IDS =['@kino_kodlar_t']
DB_PATH = "database/bot.db"  # Ma’lumotlar bazasi fayli
REFERRAL_BONUS = 5  # Referal uchun bonus chegarasi
PAYME_TOKEN = "YOUR_PAYME_TOKEN"  # Payme to‘lov tizimi tokeni
CLICK_TOKEN = "YOUR_CLICK_TOKEN"  # Click to‘lov tizimi tokeni
APELSIN_TOKEN = "YOUR_APELSIN_TOKEN"  # Apelsin to‘lov tizimi tokeni
KANAL=2052256946
CHANNEL_ID = -1002791951751  # Kanal ID manfiy belgili bo'lishi kerak
