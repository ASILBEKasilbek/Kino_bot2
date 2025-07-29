# KinoBot Pro++

🎬 **KinoBot Pro++** — bu Telegram orqali kinolar tarqatish, AI tavsiyalari, premium obunalar va gamifikatsiya tizimi bilan to‘ldirilgan avtomatlashtirilgan bot.

## Xususiyatlar
- **Kino kodi orqali yuborish**: `/get_video KINO123`
- **Freemium model**: Bepul va premium kinolar
- **Obuna paketlari**: Kundalik, haftalik, oylik (Payme, Click, Apelsin)
- **AI tavsiyasi**: `/recommend` orqali shaxsiy tavsiyalar
- **Referral tizimi**: Do‘st taklifi uchun bonuslar
- **Gamification**: XP va medallar
- **Admin paneli**: Telegram orqali to‘liq boshqaruv (`/admin_panel`)
- **Anti-piratlik**: Tokenli havolalar va monitoring
- **Ovozli buyruqlar**: Ovoz orqali kino qidirish va so‘rash
- **Kunlik eslatmalar**: Har kuni yangi kino tavsiyasi

## O‘rnatish
1. `pip install -r requirements.txt`
2. `config.py` da tokenlarni sozlang
3. Ma’lumotlar bazasini ishga tushirish: `python -m database.db`
4. Botni ishga tushirish: `python main.py`

## Foydalanish
- `/start`: Botni ishga tushirish
- `/get_video <kod>`: Kino olish
- `/recommend`: AI tavsiyasi
- `/buy_subscription`: Premium obuna
- `/admin_panel`: Adminlar uchun boshqaruv paneli
