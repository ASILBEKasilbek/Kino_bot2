import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referral_count INTEGER DEFAULT 0,
            subscription_plan TEXT,
            subscription_end TEXT,
            is_blocked INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            last_activity TEXT,
            message_count INTEGER DEFAULT 0,
            last_message_time TEXT,
            registration_date TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # Movies jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            movie_code TEXT UNIQUE,
            title TEXT,
            genre TEXT,
            year INTEGER,
            description TEXT,
            is_premium INTEGER,
            view_count INTEGER DEFAULT 0
        )
    ''')
    
    # Feedback jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            comment TEXT,
            rating INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    
    # Playlists jadvali
    # Playlists jadvali (created_at qo‘shildi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    
    # Playlist_movies jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS playlist_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER,
            movie_id INTEGER,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    
    # Upcoming_movies jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS upcoming_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            genre TEXT,
            expected_release TEXT,
            description TEXT
        )
    ''')
    
    # Notifications jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            notified INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES upcoming_movies(id)
        )
    ''')
    
    # Offline_cache jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS offline_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            movie_id INTEGER,
            expiry DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    
    # Bonuses jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bonus_description TEXT,
            awarded_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Social_posts jadvali
    c.execute('''
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            posted_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    schedule_time DATETIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
)
        ''')

    conn.commit()
    conn.close()
