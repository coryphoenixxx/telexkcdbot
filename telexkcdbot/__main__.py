import asyncio

from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling, start_webhook

from bot import bot
from config import ADMIN_ID, DEV, PORT, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.default import register_default_commands
from logger import logger
from middlewares.big_brother import big_brother
from middlewares.localization import localization
from telexkcdbot.checker import checker
from telexkcdbot.databases.comics_initial_fill import comics_initial_fill
from telexkcdbot.databases.database import db
from telexkcdbot.web.server import web_server_start

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


async def on_startup(dp: Dispatcher):
    if not DEV:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    dp.middleware.setup(localization)
    dp.middleware.setup(big_brother)

    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

    await db.create()
    await comics_initial_fill()
    await db.users.add_user(ADMIN_ID)

    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)

    asyncio.create_task(checker())

    logger.info("Bot started.")

    await web_server_start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    if DEV:
        start_polling(dispatcher=dp, skip_updates=True, on_startup=on_startup)
    else:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT,
        )
