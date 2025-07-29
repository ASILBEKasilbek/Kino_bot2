
import sqlite3
from config import DB_PATH


def get_movie_by_code(code: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, file_id, title, genre, year, description, is_premium
        FROM movies WHERE movie_code = ?
    """, (code,))
    result = c.fetchone()
    conn.close()
    return result



def update_view_count(movie_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE movies SET view_count = view_count + 1 WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()

def search_movies(query: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE title LIKE ? OR genre LIKE ? OR year LIKE ?",
              ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    movies = c.fetchall()
    conn.close()
    return movies

def get_top_movies(limit: int = 5):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # bu natijani dict sifatida olishga yordam beradi
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY view_count DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()

    # Har bir row ni dict ga aylantiramiz
    return [dict(row) for row in rows]