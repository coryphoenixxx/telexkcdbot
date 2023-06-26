import platform
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from src.api_client import api
from src.bot_instance import bot
from src.checker import checker
from src.comics_initial_fill import comics_initial_fill
from src.bot_config import ADMIN_ID, BOT_PORT, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL
from src.handlers.admin import register_admin_handlers
from src.handlers.callbacks import register_callbacks
from src.handlers.default import register_default_commands
from src.middlewares.big_brother import big_brother
from src.middlewares.localization import localization
from loguru import logger
import asyncio

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

    await bot.send_message(
        ADMIN_ID,
        text=f"""<b>❗ Bot started.</b>

<b>======== Platform Info ========</b>
<b>System:</b> {platform.uname().system}
<b>Node Name:</b> {platform.uname().node}
<b>Release:</b> {platform.uname().release}
<b>Version:</b> {platform.uname().version}
<b>Machine:</b> {platform.uname().machine}""",
        disable_notification=True,
    )

    #asyncio.create_task(checker())

    logger.info("Bot started.")


async def on_shutdown(dp: Dispatcher):
    # TODO
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
