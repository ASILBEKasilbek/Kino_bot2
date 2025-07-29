from config import DB_PATH
import sqlite3
from datetime import datetime, timedelta

def is_piracy_suspected(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message_count, last_message_time FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return False
    
    message_count, last_message_time = user
    last_message_time = datetime.strptime(last_message_time, "%Y-%m-%d %H:%M:%S") if last_message_time else datetime.now() - timedelta(seconds=10)
    
    if (datetime.now() - last_message_time).total_seconds() < 2 and message_count > 5:
        conn.close()
        return True
    
    conn.close()
    return False
