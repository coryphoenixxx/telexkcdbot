import asyncio
import aioschedule
import asyncpg

from aiogram import Dispatcher
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot import bot
from loguru import logger
from config import HEROKU, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL, PORT, ADMIN_ID, DATABASE_URL, LOGS_DIR
from common_utils import get_and_broadcast_new_comic
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.default import register_default_commands
from middlewares.big_brother import big_brother
from middlewares.localization import localization
from src.telexkcdbot.databases.fill_comics_db import initial_filling_of_comics_db
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db


async def checker():
    await get_and_broadcast_new_comic()
    aioschedule.every(0.25).minutes.do(get_and_broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def on_startup(dp: Dispatcher):
    if HEROKU:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await users_db.add_user(ADMIN_ID)
    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)
    asyncio.create_task(checker())
    logger.info("Bot started.")


def create_pool(db_url: str) -> asyncpg.Pool:
    if HEROKU:
        db_url += '?sslmode=require'
    return asyncpg.create_pool(db_url, max_size=20)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    storage = MemoryStorage()

    dp = Dispatcher(bot, loop=loop, storage=storage)

    dp.middleware.setup(localization)
    dp.middleware.setup(big_brother)

    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

    pool = loop.run_until_complete(create_pool(DATABASE_URL))
    loop.run_until_complete(users_db.create(pool))
    loop.run_until_complete(comics_db.create(pool))

    loop.run_until_complete(initial_filling_of_comics_db())

    logger.add(f'{LOGS_DIR}/actions.log', rotation='5 MB', level='INFO')
    logger.add(f'{LOGS_DIR}/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
    logger.error("Log files created...")  # Creates both log files

    if HEROKU:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT
        )
    else:
        start_polling(dispatcher=dp,
                      skip_updates=True,
                      on_startup=on_startup)
