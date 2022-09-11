import asyncio

import aioschedule
import asyncpg
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling, start_webhook
from aiohttp import web
from loguru import logger

from bot import bot
from comic_data_getter import comics_data_getter
from common_utils import broadcast
from config import (
    ADMIN_ID,
    DATABASE_URL,
    HEROKU,
    LOGS_DIR,
    PORT,
    WEBAPP_HOST,
    WEBHOOK_PATH,
    WEBHOOK_URL,
)
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.default import register_default_commands
from middlewares.big_brother import big_brother
from middlewares.localization import localization
from models import TotalComicData
from telexkcdbot.databases.comics_db import comics_db
from telexkcdbot.databases.fill_comics_db import initial_filling_of_comics_db
from telexkcdbot.databases.users_db import users_db


async def get_and_broadcast_new_comic() -> None:
    db_last_comic_id = await comics_db.get_last_comic_id()

    if not db_last_comic_id:  # If Heroku database is down then skip the check
        return

    real_last_comic_id = await comics_data_getter.get_xkcd_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            xkcd_comic_data = await comics_data_getter.get_xkcd_comic_data_by_id(comic_id)

            await comics_db.add_new_comic(
                TotalComicData(
                    comic_id=xkcd_comic_data.comic_id,
                    title=xkcd_comic_data.title,
                    img_url=xkcd_comic_data.img_url,
                    comment=xkcd_comic_data.comment,
                    public_date=xkcd_comic_data.public_date,
                )
            )
        await broadcast(comic_id=real_last_comic_id)


async def checker() -> None:
    await get_and_broadcast_new_comic()
    aioschedule.every(15).minutes.do(get_and_broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(300)


async def on_startup(dp: Dispatcher) -> None:
    if HEROKU:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await users_db.add_user(ADMIN_ID)
    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)
    asyncio.create_task(checker())
    logger.info("Bot started.")
    await start_server()


def create_pool(db_url: str) -> asyncpg.Pool:
    if HEROKU:
        db_url += "?sslmode=require"
    return asyncpg.create_pool(db_url, max_size=20)


async def hello(request: web.Request) -> web.Response:
    print("GET")
    return web.Response(text="Hello, world!")


async def start_server() -> None:
    loop = asyncio.get_event_loop()
    app = web.Application()
    app.add_routes([web.get("/", handler=hello)])
    runner = web.AppRunner(app)
    await runner.setup()
    await loop.create_server(runner.server, "127.0.0.1", 8080)
    print("Server started at http://127.0.0.1:8080")


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

    logger.add(f"{LOGS_DIR}/actions.log", rotation="5 MB", level="INFO")
    logger.add(
        f"{LOGS_DIR}/errors.log",
        rotation="500 KB",
        level="ERROR",
        backtrace=True,
        diagnose=True,
    )
    logger.error("Log files created...")  # Creates both log files

    if HEROKU:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT,
        )
    else:
        start_polling(dispatcher=dp, skip_updates=True, on_startup=on_startup)