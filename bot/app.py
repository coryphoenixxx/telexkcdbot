import aioschedule

from datetime import date

from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from aiogram.utils.executor import start_webhook, start_polling

from bot.config import *
from bot.funcs import *
from bot.fill_comics_db import fill_comics_db


class BigBrother(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(BigBrother, self).__init__()

    @staticmethod
    async def on_pre_process_update(update: Update, data: dict):
        action_date = date.today()

        if update.message:
            msg = update.message
            user_id = msg.from_user.id

            if user_id != ADMIN_ID:
                text = await preprocess_text(msg.text)
                logger.info(f"{user_id}|{msg.from_user.username}|{msg.from_user.language_code}|text:'{text}'")

            await users_db.update_last_action_date(user_id, action_date)

        if update.callback_query:
            call = update.callback_query
            user_id = call.from_user.id

            if user_id != ADMIN_ID:
                logger.info(f"{user_id}|{call.from_user.username}|{call.from_user.language_code}|call:'{call.data}'")

            await users_db.update_last_action_date(user_id, action_date)

    """ANTIFLOOD"""
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
            await message.reply('❗❗❗ <b>Too many requests!</b>')

        await asyncio.sleep(delta)

        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await asyncio.sleep(2)
            await message.reply('❗ <b>Unlocked.</b>')


async def get_and_broadcast_new_comic():
    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = await parser.xkcd_latest_comic_id

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            comic_data = await parser.get_full_comic_data(comic_id)
            await comics_db.add_new_comic(comic_data)

        comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
        all_users_ids = await users_db.get_all_users_ids()

        await broadcast(all_users_ids,
                        text="🔥 <b>And here\'s new comic!</b> 🔥",
                        comic_data=comic_data)


async def checker():
    await get_and_broadcast_new_comic()
    delay = 5
    aioschedule.every(delay).minutes.do(get_and_broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)


async def on_startup(dp: Dispatcher):
    if HEROKU:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    asyncio.create_task(checker())
    await users_db.add_user(ADMIN_ID)

    await bot.send_message(ADMIN_ID, text="<b>❗ Bot started.</b>")

    logger.error("Bot started.")  # Creates log files (both)


if __name__ == "__main__":
    from bot.handlers import dp

    dp.middleware.setup(BigBrother())
    loop.run_until_complete(fill_comics_db())

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
