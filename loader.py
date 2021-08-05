import asyncio


from aiogram import Bot
from aiogram.types import ParseMode


from databases import ComicsDatabase, UsersDatabase
from config_ import API_TOKEN
from loguru import logger


users_db = UsersDatabase()
comics_db = ComicsDatabase()

loop = asyncio.get_event_loop()
bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)

logger.add('actions.log', rotation='5 MB', level='INFO')
logger.add('errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
