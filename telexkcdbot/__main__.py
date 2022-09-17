import asyncio

import aioschedule
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from loguru import logger

from bot import bot
from comic_data_getter import comics_data_getter
from common_utils import broadcast
from config import ADMIN_ID, LOGS_DIR
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.default import register_default_commands
from middlewares.big_brother import big_brother
from middlewares.localization import localization
from models import TotalComicData
from telexkcdbot.databases.comics_initial_fill import comics_initial_fill
from telexkcdbot.databases.database import db
from telexkcdbot.web.server import web_server_start


async def get_and_broadcast_new_comic() -> None:
    db_last_comic_id = await db.comics.get_last_comic_id()

    if not db_last_comic_id:  # If Heroku database is down then skip the check
        return

    real_last_comic_id = await comics_data_getter.get_xkcd_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            xkcd_comic_data = await comics_data_getter.get_xkcd_comic_data_by_id(comic_id)

            await db.comics.add_new_comic(
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
    await db.users.add_user(ADMIN_ID)
    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)
    asyncio.create_task(checker())
    logger.info("Bot started.")


async def main():
    storage = MemoryStorage()

    dp = Dispatcher(bot, storage=storage)

    dp.middleware.setup(localization)
    dp.middleware.setup(big_brother)

    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

    await db.create()
    await comics_initial_fill()

    logger.add(f"{LOGS_DIR}/actions.log", rotation="5 MB", level="INFO")
    logger.add(
        f"{LOGS_DIR}/errors.log",
        rotation="500 KB",
        level="ERROR",
        backtrace=True,
        diagnose=True,
    )
    logger.error("Log files created...")  # Creates both log files

    tasks = [dp.start_polling(), web_server_start()]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
