import asyncio


from aiogram import Bot
from aiogram.types import ParseMode, Message


from databases import ComicsDatabase, UsersDatabase
from config_ import API_TOKEN, ADMIN_ID
from loguru import logger
from string import ascii_letters, digits


users_db = UsersDatabase()
comics_db = ComicsDatabase()

loop = asyncio.get_event_loop()
bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)

logger.add('actions.log', rotation='5 MB', level='INFO')
logger.add('errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)


async def preprocess_text(text: str):
    text = text.strip()
    permitted = ascii_letters + digits + 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя' + ' '
    text = ''.join([ch for ch in text if ch in permitted])
    return text[:30]


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


def admin(func):
    async def decorator(msg: Message):
        if msg.from_user.id != int(ADMIN_ID):
            await msg.answer('Nope!)))')
        else:
            await func(msg)
    return decorator
