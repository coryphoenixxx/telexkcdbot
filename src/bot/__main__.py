import asyncio

from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from api_client import api
from bot import bot
from checker import checker
from comics_initial_fill import comics_initial_fill
from config import ADMIN_ID, BOT_PORT, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.default import register_default_commands
from loguru import logger
from middlewares.big_brother import big_brother
from middlewares.localization import localization

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


async def on_startup(dp: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    dp.middleware.setup(localization)
    dp.middleware.setup(big_brother)

    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

    await api.check_connection()
    await comics_initial_fill()

    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>", disable_notification=True)

    asyncio.create_task(checker())

    logger.info("Bot started.")


async def on_shutdown(dp: Dispatcher):
    pass


if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=BOT_PORT,
    )
