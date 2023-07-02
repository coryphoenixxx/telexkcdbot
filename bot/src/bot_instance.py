"""For sharing bot instance between modules."""

from aiogram import Bot
from aiogram.types import ParseMode
from src.bot_config import TG_API_TOKEN

bot = Bot(TG_API_TOKEN, parse_mode=ParseMode.HTML)
