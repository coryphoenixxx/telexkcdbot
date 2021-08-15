import asyncio

from aiogram import Bot
from aiogram.types import ParseMode

from databases import ComicsDatabase, UsersDatabase, create_pool
from config import API_TOKEN
from loguru import logger
from xkcd_parser import Parser

loop = asyncio.get_event_loop()
pool = loop.run_until_complete(create_pool())

users_db = UsersDatabase(pool)
comics_db = ComicsDatabase(pool)
parser = Parser()

loop.run_until_complete(users_db.create())
loop.run_until_complete(comics_db.create())
loop.run_until_complete(parser.create())

bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)

logger.add('./logs/actions.log', rotation='5 MB', level='INFO')
logger.add('./logs/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
