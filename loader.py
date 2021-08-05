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


async def preprocess_text(text: str):
    from string import ascii_letters, digits
    permissible = ascii_letters + digits + ' '
    text = ''.join([c for c in text if c in permissible])
    return text[:30].strip()


def rate_limit(limit: int, key=None):
    """
    Decorator for configuring rate limit and key in different functions.
    """
    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator
