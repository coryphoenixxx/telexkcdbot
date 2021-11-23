import asyncio

from datetime import date
from loguru import logger

from aiogram import Dispatcher
from aiogram.types import Update, Message
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from telexkcdbot.common_utils import preprocess_text, remove_prev_message_kb, user_is_unavailable
from telexkcdbot.config import ADMIN_ID
from telexkcdbot.keyboards import kboard
from telexkcdbot.databases.users_db import users_db
from telexkcdbot.middlewares.localization import _


class BigBrother(BaseMiddleware):
    def __init__(self, limit: float = DEFAULT_RATE_LIMIT, key_prefix: str = 'antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(BigBrother, self).__init__()

    @staticmethod
    async def on_pre_process_update(update: Update, data: dict):
        if not update.my_chat_member:
            user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
            username = update.message.from_user.username if update.message else update.callback_query.from_user.username
            language_code = update.message.from_user.language_code if update.message \
                else update.callback_query.from_user.language_code

            if user_id != ADMIN_ID:  # Don't log admin actions
                if await user_is_unavailable(user_id):
                    pass
                else:
                    if update.callback_query:
                        logger.info(f"{user_id}|{username}|{language_code}|call:{update.callback_query.data}")
                    elif update.message.text:
                        text = preprocess_text(update.message.text)
                        if text:
                            logger.info(f"{user_id}|{username}|{language_code}|text:{text}")
                    else:
                        logger.info(f"{user_id}|{username}|{language_code}|<other>")

            action_date = date.today()
            try:
                await users_db.update_last_action_date(user_id, action_date)
            except Exception as err:
                logger.error(f"Couldn't update last action date ({user_id}, {action_date}): {err}")

    """ANTIFLOOD"""

    async def on_process_message(self, msg: Message, data: dict):
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
            await self.message_throttled(msg, t)
            raise CancelHandler()

    async def message_throttled(self, msg: Message, throttled: Throttled):
        """
        Notify user only on first exceed and notify about unlocking only on last exceed
        """
        await remove_prev_message_kb(msg)

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
            await msg.reply(_('❗❗❗ <b>Too many requests!</b>'))

        await asyncio.sleep(delta)

        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await msg.reply(_('❗ <b>Unlocked.</b>'), reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))


big_brother = BigBrother()
