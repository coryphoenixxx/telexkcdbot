import asyncio

from aiogram import Bot
from aiogram.types import ParseMode

from loguru import logger
from pathlib import Path

from .databases import ComicsDatabase, UsersDatabase, create_pool
from .config import API_TOKEN, DATABASE_URL, HEROKU

if HEROKU:
    image_path = '/app/static/img'
    logs_path = '/app/logs'
    path_to_json = '/app/static/ru_data_from_xkcd_ru_tg_channel.json'
else:
    image_path = Path.cwd().parent.parent / 'static/img'
    logs_path = Path.cwd().parent.parent / 'logs'
    path_to_json = Path.cwd().parent.parent / 'static/ru_data_from_xkcd_ru_tg_channel.json'

from .xkcd_parser import Parser

bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
loop = asyncio.get_event_loop()
pool = loop.run_until_complete(create_pool(DATABASE_URL))

users_db = UsersDatabase(pool)
comics_db = ComicsDatabase(pool)
parser = Parser()

loop.run_until_complete(users_db.create())
loop.run_until_complete(comics_db.create())
loop.run_until_complete(parser.create())

logger.add(f'{logs_path}/actions.log', rotation='5 MB', level='INFO')
logger.add(f'{logs_path}/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
