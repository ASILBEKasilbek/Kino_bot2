
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup



def movie_buttons(movie_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Watchlist", callback_data=f"watchlist_add_{movie_id}")],
            [
                InlineKeyboardButton(text="⭐1", callback_data=f"rate_{movie_id}_1"),
                InlineKeyboardButton(text="⭐2", callback_data=f"rate_{movie_id}_2"),
                InlineKeyboardButton(text="⭐3", callback_data=f"rate_{movie_id}_3"),
                InlineKeyboardButton(text="⭐4", callback_data=f"rate_{movie_id}_4"),
                InlineKeyboardButton(text="⭐5", callback_data=f"rate_{movie_id}_5"),
            ]
        ]
    )



