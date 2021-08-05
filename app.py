import asyncio
import aioschedule

from aiogram import Dispatcher
from aiogram.types import Update, Message
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled, BotBlocked, UserDeactivated
from aiogram.utils.executor import start_webhook, start_polling
from pathlib import Path

from loader import users_db, comics_db, bot, logger, preprocess_text
from parser_ import parser
from config_ import *
from handlers import send_comic


async def broadcast_new_comic():
    async def get_subscribed_users():
        for user_id in (await users_db.subscribed_users):
            yield user_id

    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = parser.latest_comic_id

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            data = await parser.get_full_comic_data(comic_id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            async for user_id in get_subscribed_users():
                try:
                    await bot.send_message(user_id, "<b>🔥 And here\'s new comic!</b> 🔥")
                except (BotBlocked, UserDeactivated):
                    await users_db.delete_user(user_id)
                    continue

                comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
                await send_comic(user_id, data=comic_data)
                count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
        except Exception as err:
            logger.error("Can't send new comic!", err)
        finally:
            await bot.send_message(ADMIN_ID, f"{count} messages were successfully sent.")


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

    if HEROKU:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    await bot.send_message(chat_id=ADMIN_ID, text="<b>I'm here, in Your Power, My Lord...</b>")

    logger.info("Bot started.")


"""ANTIFLOOD FROM DOC"""


class BigBrother(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(BigBrother, self).__init__()

    @staticmethod
    async def on_pre_process_update(update: Update, data: dict):
        if update.message:
            msg = update.message
            text = await preprocess_text(msg.text)
            logger.info(f"{msg.from_user.id} | {msg.from_user.username} | {msg.from_user.language_code} | "
                        f"text:'{text}' | utc: {msg.date.utcnow()}")
        if update.callback_query:
            call = update.callback_query
            logger.info(f"{call.from_user.id} | {call.from_user.username} | {call.from_user.language_code} | "
                        f"call:'{call.data}' | utc: {call.message.date.utcnow()}")

    async def on_process_message(self, message: Message, data: dict):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        # If handler was configured, get rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: Message, throttled: Throttled):
        """
        Notify user only on first exceed and notify about unlocking only on last exceed
        """
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = (throttled.rate - throttled.delta)

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply('❗❗❗ Too many requests! ')

        await asyncio.sleep(delta)

        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await asyncio.sleep(2)
            await message.reply('Unlocked.')


if __name__ == "__main__":
    from handlers import dp

    dp.middleware.setup(BigBrother())

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

        # import subprocess
        #
        # DETACHED_PROCESS = 0x00000008
        # subprocess.Popen('./redis/redis-server.exe', creationflags=DETACHED_PROCESS, close_fds=True)
        start_polling(dispatcher=dp,
                      skip_updates=True,
                      on_startup=on_startup)
