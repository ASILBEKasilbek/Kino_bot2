import unittest
from core.ai_recommendation import get_movie_recommendations
from config import DB_PATH
import sqlite3

class TestAIRecommendation(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.c = self.conn.cursor()
        self.c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (999, "test_user"))
        self.c.execute("INSERT OR IGNORE INTO movies (file_id, movie_code, title, genre, year, description, is_premium) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("file123", "KINO123", "Test Movie", "Action", 2020, "Test description", 0))
        self.conn.commit()
    
    def test_get_recommendations(self):
        recommendations = get_movie_recommendations(999, genre="Action")
        self.assertTrue(len(recommendations) <= 5)
        if recommendations:
            self.assertEqual(recommendations[0][2], "Action")
    
    def tearDown(self):
        self.c.execute("DELETE FROM users WHERE user_id = ?", (999,))
        self.c.execute("DELETE FROM movies WHERE movie_code = ?", ("KINO123",))
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    unittest.main()
