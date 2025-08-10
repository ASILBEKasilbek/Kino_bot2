
import sqlite3
from config import DB_PATH

def get_all_channels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

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
def add_to_watchlist(user_id: int, movie_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_watchlist(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT m.id, m.title, m.movie_code 
        FROM watchlist w
        JOIN movies m ON w.movie_id = m.id
        WHERE w.user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows
def set_rating(user_id: int, movie_id: int, rating: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO ratings (user_id, movie_id, rating)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, movie_id) DO UPDATE SET rating = excluded.rating
    """, (user_id, movie_id, rating))
    conn.commit()
    conn.close()

def get_average_rating(movie_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(rating) FROM ratings WHERE movie_id=?", (movie_id,))
    avg = c.fetchone()[0]
    conn.close()
    return round(avg, 1) if avg else None

def get_all_ratings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM ratings")
    rows = c.fetchall()
    print(rows)
    conn.close()
    return rows

def get_recommendations_by_genre(user_id: int, limit: int = 5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Foydalanuvchi oxirgi ko‘rgan film janrini olish
    c.execute("""
        SELECT genre FROM movies m
        JOIN (
            SELECT movie_id FROM offline_cache WHERE user_id = ? 
            ORDER BY expiry DESC LIMIT 1
        ) AS last_movie ON m.id = last_movie.movie_id
    """, (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return []

    genre = row[0]
    c.execute("""
        SELECT id, title, movie_code FROM movies 
        WHERE genre = ? ORDER BY RANDOM() LIMIT ?
    """, (genre, limit))
    movies = c.fetchall()
    conn.close()
    return movies
