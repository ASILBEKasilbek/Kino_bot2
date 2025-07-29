from config import DB_PATH
import sqlite3
from datetime import datetime

def get_cached_movies(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT m.title, m.genre, m.year, c.file_id FROM offline_cache c JOIN movies m ON c.movie_id = m.id WHERE c.user_id = ? AND c.expiry > ?",
              (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cached_movies = c.fetchall()
    conn.close()
    return cached_movies