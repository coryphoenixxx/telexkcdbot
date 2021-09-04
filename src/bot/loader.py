import asyncio

from aiogram import Bot
from aiogram.types import ParseMode

from loguru import logger
from pathlib import Path

from src.bot.databases import ComicsDatabase, UsersDatabase, create_pool
from src.bot.config import API_TOKEN, DATABASE_URL
from src.bot.xkcd_parser import Parser


bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
loop = asyncio.get_event_loop()
pool = loop.run_until_complete(create_pool(DATABASE_URL))

image_path = Path.cwd().parent.parent.joinpath('static/img')
logs_path = Path.cwd().parent.parent.joinpath('logs')

users_db = UsersDatabase(pool)
comics_db = ComicsDatabase(pool)
parser = Parser()

loop.run_until_complete(users_db.create())
loop.run_until_complete(comics_db.create())
loop.run_until_complete(parser.create())

logger.add(f'{logs_path}/actions.log', rotation='5 MB', level='INFO')
logger.add(f'{logs_path}/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)


