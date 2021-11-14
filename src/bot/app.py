import asyncio
import aioschedule

from datetime import date
from asyncpg import CannotConnectNowError

from aiogram import Dispatcher
from aiogram.types import Update, ChatActions, Message
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled, BotBlocked, UserDeactivated, ChatNotFound, InvalidPeerID
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.bot.config import HEROKU, WEBAPP_HOST, WEBHOOK_PATH, WEBHOOK_URL, PORT, ADMIN_ID
from src.bot.utils import preprocess_text, broadcast
from src.bot.loader import bot, loop, users_db, comics_db, parser
from src.bot.fill_comics_db import initial_filling_of_comics_db
from src.bot.logger import logger
from src.bot.handlers.admin import register_admin_handlers
from src.bot.handlers.callbacks import register_callbacks
from src.bot.handlers.default import register_default_commands


class BigBrother(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(BigBrother, self).__init__()

    @staticmethod
    async def on_pre_process_update(update: Update, data: dict):
        if update.message or update.callback_query:
            user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
            action_date = date.today()

            if user_id != ADMIN_ID:
                username, user_lang, action = ('',) * 3
                try:
                    await bot.send_chat_action(user_id, ChatActions.TYPING)
                except (BotBlocked, UserDeactivated, ChatNotFound, InvalidPeerID):
                    pass
                else:
                    if update.callback_query:
                        call = update.callback_query
                        username = call.from_user.username
                        user_lang = call.from_user.language_code
                        action = f"call: {call.data}"
                    elif update.message.text:
                        msg = update.message
                        username = msg.from_user.username
                        user_lang = msg.from_user.language_code
                        action = f"text: {await preprocess_text(msg.text)}"

                    logger.info(f"{user_id}|{username}|{user_lang}|{action}")

            try:
                await users_db.update_last_action_date(user_id, action_date)
            except CannotConnectNowError:
                logger.error(f"Couldn't update last action date ({user_id}, {action_date})")

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

    if not db_last_comic_id:  # While heroku database is down, skip the check
        return

    real_last_comic_id = await parser.get_xkcd_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            comic_data = tuple((await parser.get_en_comic_data_by_id(comic_id)).values()) + ('',)*3
            await comics_db.add_new_comic(comic_data)

        comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
        await broadcast(text="🔥 <b>And here comes the new comic!</b> 🔥",
                        comic_data=comic_data)


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

    logger.error("Bot started.")  # Creates log files (both)


if __name__ == "__main__":
    storage = MemoryStorage()
    dp = Dispatcher(bot, loop=loop, storage=storage)

    dp.middleware.setup(BigBrother())

    register_admin_handlers(dp)
    register_callbacks(dp)
    register_default_commands(dp)

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
