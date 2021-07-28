import asyncio


from aiogram import Bot
from aiogram.types import ParseMode


from database_ import ComicsDatabase, UsersDatabase
from config_ import API_TOKEN


users_db = UsersDatabase()
comics_db = ComicsDatabase()

loop = asyncio.get_event_loop()
bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
