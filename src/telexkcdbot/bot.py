from aiogram import Bot
from aiogram.types import ParseMode

from src.telexkcdbot.config import API_TOKEN


bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
