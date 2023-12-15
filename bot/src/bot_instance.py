"""For sharing bot (deprecated) instance between modules."""

from aiogram import Bot
from aiogram.types import ParseMode

from api import TG_API_TOKEN

bot = Bot(TG_API_TOKEN, parse_mode=ParseMode.HTML)
