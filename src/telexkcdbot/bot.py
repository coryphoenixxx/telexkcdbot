# For sharing bot instance between modules

from aiogram import Bot
from aiogram.types import ParseMode

from config import API_TOKEN


bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
