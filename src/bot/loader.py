import asyncio

from aiogram import Bot
from aiogram.types import ParseMode


from .databases import ComicsDatabase, UsersDatabase, create_pool
from .config import API_TOKEN, DATABASE_URL

bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
loop = asyncio.get_event_loop()
pool = loop.run_until_complete(create_pool(DATABASE_URL))

users_db = UsersDatabase(pool)
comics_db = ComicsDatabase(pool)

# TODO: переделать
from .xkcd_parser import Parser
parser = Parser()

loop.run_until_complete(users_db.create())
loop.run_until_complete(comics_db.create())
loop.run_until_complete(parser.create())
