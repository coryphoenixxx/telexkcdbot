import asyncio
import aioschedule
import asyncpg

from aiogram import Dispatcher
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.telexkcdbot.config import HEROKU, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL, PORT, ADMIN_ID, DATABASE_URL
from src.telexkcdbot.common_utils import broadcast
from src.telexkcdbot.bot import bot
from src.telexkcdbot.databases.fill_comics_db import initial_filling_of_comics_db
from src.telexkcdbot.logger import logger
from src.telexkcdbot.handlers.admin import register_admin_handlers
from src.telexkcdbot.handlers.callbacks import register_callbacks
from src.telexkcdbot.handlers.default import register_default_commands
from src.telexkcdbot.xkcd_parser import parser
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.middlewares.big_brother import BigBrother


async def get_and_broadcast_new_comic():
    db_last_comic_id = await comics_db.get_last_comic_id()

    if not db_last_comic_id:  # While heroku database is down, skip the check
        return

    real_last_comic_id = await parser.get_xkcd_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            comic_data = tuple((await parser.get_en_comic_data_by_id(comic_id)).values()) + ('', '', '', False)
            await comics_db.add_new_comic(comic_data)

        await broadcast(text="🔥 <b>And here comes the new comic!</b> 🔥",
                        comic_id=real_last_comic_id)


async def checker():
    await get_and_broadcast_new_comic()
    aioschedule.every(2).minutes.do(get_and_broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)


async def on_startup(dp: Dispatcher):
    if HEROKU:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    await users_db.add_user(ADMIN_ID)
    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)
    asyncio.create_task(checker())

    logger.info("Bot started.")


def create_pool(db_url) -> asyncpg.Pool:
    if HEROKU:
        db_url += '?sslmode=require'
    return asyncpg.create_pool(db_url, max_size=20)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    storage = MemoryStorage()

    dp = Dispatcher(bot, loop=loop, storage=storage)
    dp.middleware.setup(BigBrother())
    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

    pool = loop.run_until_complete(create_pool(DATABASE_URL))

    loop.run_until_complete(users_db.create(pool))
    loop.run_until_complete(comics_db.create(pool))

    loop.run_until_complete(initial_filling_of_comics_db())

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
