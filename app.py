import asyncio
import aioschedule
from pathlib import Path

from aiogram import Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Update
from aiogram.utils.executor import start_webhook, start_polling

from loader import users_db, bot, logger
from config_ import *
from handlers import broadcast_new_comic


async def checker():
    await broadcast_new_comic()
    delay = 15
    aioschedule.every(delay).minutes.do(broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)


async def cleaner():
    async def clean():
        logs = list(Path.cwd().glob('*.log'))
        for log in logs:
            if log.name not in ('actions.log', 'errors.log'):
                log.unlink()
    await clean()
    delay = 12
    aioschedule.every(delay).hours.do(clean)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(3600)


async def on_startup(dp: Dispatcher):
    await users_db.create()
    await users_db.add_user(ADMIN_ID)
    asyncio.create_task(checker())
    asyncio.create_task(cleaner())
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await bot.send_message(chat_id=ADMIN_ID, text="<b>I'm here, in Your Power, My Lord...</b>")
    logger.info("Bot started.")


class BigBrother(BaseMiddleware):
    @staticmethod
    async def on_pre_process_update(update: Update, data: dict):
        if update.message:
            msg = update.message
            logger.info(f"{msg.from_user.id} | {msg.from_user.username} | {msg.from_user.language_code} | "
                        f"text:'{msg.text}' | utc: {msg.date.utcnow()}")
        if update.callback_query:
            call = update.callback_query
            logger.info(f"{call.from_user.id} | {call.from_user.username} | {call.from_user.language_code} | "
                        f"call:'{call.data}' | utc: {call.message.date.utcnow()}")


if __name__ == "__main__":
    from handlers import dp

    dp.middleware.setup((BigBrother()))

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
        # run redis locally on windows (https://github.com/downloads/dmajkic/redis/redis-2.4.5-win32-win64.zip)
        import subprocess

        DETACHED_PROCESS = 0x00000008
        subprocess.Popen('./redis/redis-server.exe', creationflags=DETACHED_PROCESS, close_fds=True)
        start_polling(dispatcher=dp,
                      skip_updates=True,
                      on_startup=on_startup)
