import unittest
from aiogram.types import Message
from handlers.start import start_command
from config import DB_PATH
import sqlite3
from unittest.mock import AsyncMock

class TestHandlers(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.c = self.conn.cursor()
        self.message = AsyncMock(spec=Message)
        self.message.from_user.id = 999
        self.message.from_user.username = "test_user"
        self.message.text = "/start"
    
    async def test_start_command(self):
        await start_command(self.message)
        self.c.execute("SELECT user_id FROM users WHERE user_id = ?", (999,))
        user = self.c.fetchone()
        self.assertIsNotNone(user)
    
    def tearDown(self):
        self.c.execute("DELETE FROM users WHERE user_id = ?", (999,))
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    unittest.main()
