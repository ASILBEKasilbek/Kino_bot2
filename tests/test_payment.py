import unittest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, CallbackQuery
from core.payment import buy_subscription_command
from config import DB_PATH
import sqlite3

class TestPayment(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.c = self.conn.cursor()
        self.message = AsyncMock(spec=Message)
        self.message.from_user.id = 999
        self.message.text = "/buy_subscription"
    
    @patch("requests.post")
    async def test_buy_subscription(self, mock_post):
        mock_post.return_value.status_code = 200
        await buy_subscription_command(self.message, AsyncMock())
        self.message.reply.assert_called_with("💎 Obuna rejasini tanlang:")
    
    def tearDown(self):
        self.c.execute("DELETE FROM users WHERE user_id = ?", (999,))
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    unittest.main()
