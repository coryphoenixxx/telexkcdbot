from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_navigation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="|<<", callback_data="nav_first"))
    builder.add(InlineKeyboardButton(text="<Prev", callback_data="nav_prev"))
    builder.add(InlineKeyboardButton(text="🎲Rand", callback_data="nav_random"))
    builder.add(InlineKeyboardButton(text="Next>", callback_data="nav_next"))
    builder.add(InlineKeyboardButton(text=">>|", callback_data="nav_last"))

    return builder.as_markup()
