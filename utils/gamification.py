from config import DB_PATH, BOT_TOKEN
from aiogram import Bot
import sqlite3
from datetime import datetime

class Gamification:
    def __init__(self):
        self.actions = {
            "watch_movie": 10,
            "request_recommendation": 5,
            "leave_feedback": 5,
            "purchase_subscription": 50,
            "referral": 20,
            "create_playlist": 10,
            "add_to_playlist": 5,
            "add_movie": 20,
            "block_user": 15,
            "add_admin": 20,
            "remove_admin": 15,
            "add_channel": 10,
            "remove_channel": 10,
            "send_ad": 30,
            "social_post": 20,
            "request_notification": 5,
            "add_upcoming_movie": 20,
            "voice_command": 10
        }
    
    def add_xp(self, user_id: int, action: str) -> int:
        xp_to_add = self.actions.get(action, 0)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        
        if user:
            current_xp, current_level = user
            new_xp = current_xp + xp_to_add
            new_level = new_xp // 100
            
            c.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
                      (new_xp, new_level, user_id))
            
            if new_level > current_level:
                c.execute("INSERT INTO bonuses (user_id, bonus_description, awarded_at) VALUES (?, ?, ?)",
                          (user_id, f"Level {new_level} ga ko‘tarildi!", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            return new_xp
        
        conn.close()
        return 0
    
    async def award_referral_bonus(self, bot: Bot, referrer_id: int, referred_id: int):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referrer_id,))
        c.execute("INSERT INTO bonuses (user_id, bonus_description, awarded_at) VALUES (?, ?, ?)",
                  (referrer_id, "Yangi referal uchun bonus!", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        new_xp = self.add_xp(referrer_id, "referral")
        await bot.send_message(referrer_id, f"🎉 Yangi referal qo‘shildi! 📊 Yangi XP: {new_xp}")