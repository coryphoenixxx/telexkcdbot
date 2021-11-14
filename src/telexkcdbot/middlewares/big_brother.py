import asyncio
import asyncpg

from datetime import date

from aiogram import Dispatcher
from aiogram.types import Update, ChatActions, Message
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled, BotBlocked, UserDeactivated, ChatNotFound, InvalidPeerID

from src.telexkcdbot.utils import preprocess_text
from src.telexkcdbot.config import ADMIN_ID
from src.telexkcdbot.bot import bot
from src.telexkcdbot.logger import logger
from src.telexkcdbot.databases.users import users_db


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
            except asyncpg.CannotConnectNowError:
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