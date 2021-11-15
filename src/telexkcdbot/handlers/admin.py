from contextlib import suppress

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.logger import logger
from src.telexkcdbot.common_utils import broadcast
from src.telexkcdbot.handlers.handlers_utils import suppress_exceptions, remove_prev_message_kb
from src.telexkcdbot.config import ADMIN_ID
from src.telexkcdbot.paths import LOGS_PATH


class Broadcast(StatesGroup):
    waiting_for_input = State()


async def cmd_admin(msg: Message, state: FSMContext):
    if msg.from_user.id != int(ADMIN_ID):
        await msg.answer("❗ <b>For admin only!</b>")
    else:
        await remove_prev_message_kb(msg)
        await state.reset_data()

        await msg.answer("<b>*** ADMIN PANEL ***</b>",
                         reply_markup=await kboard.admin_panel())


async def cb_toggle_spec_status(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await call.message.delete()

    cur_comic_id, _ = await users_db.get_cur_comic_info(ADMIN_ID)
    await comics_db.toggle_spec_status(cur_comic_id)

    await call.message.answer(text=f"<b>*** ADMIN PANEL ***</b>\n❗ <b>It's done for {cur_comic_id}</b>",
                              reply_markup=await kboard.admin_panel())


async def cb_send_log(call: CallbackQuery):
    filename = LOGS_PATH.joinpath('actions.log') if 'actions' in call.data else LOGS_PATH.joinpath('errors.log')

    try:
        await call.message.answer_document(InputFile(filename))
    except BadRequest as err:
        logger.error(f"Couldn't send logs ({err})")


async def cb_users_info(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await call.message.delete()

    all_users_num = len(await users_db.get_all_users_ids())
    subscribed_users_num = len(await users_db.get_subscribed_users())
    active_users_num = await users_db.get_last_week_active_users_num()
    text = f"""<b>*** ADMIN PANEL ***</b>
❗
<b>Total</b>: <i>{all_users_num}</i>
<b>Subs</b>: <i>{subscribed_users_num}</i>
<b>Active</b>: <i>{active_users_num}</i>
"""
    await call.message.answer(text, reply_markup=await kboard.admin_panel())


async def cb_type_broadcast_message(call: CallbackQuery):
    await Broadcast.waiting_for_input.set()
    await call.message.answer(text="❗ <b>Type in a broadcast message (or /cancel):</b>")


async def cmd_cancel(msg: Message, state: FSMContext):
    if await state.get_state() is None:
        return

    await msg.answer(text="❗ <b>Canceled.</b>")
    await state.finish()


async def broadcast_admin_msg(msg: Message, state: FSMContext):
    text = f"❗❗❗ <b>ADMIN MESSAGE:\n</b>  {msg.text}"
    await broadcast(text=text)
    await state.finish()


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands='admin')
    dp.register_callback_query_handler(cb_users_info, text='users_info')
    dp.register_callback_query_handler(cb_toggle_spec_status, text='change_spec_status')
    dp.register_callback_query_handler(cb_send_log, Text(startswith='send_'))
    dp.register_callback_query_handler(cb_type_broadcast_message, text='broadcast_admin_msg')
    dp.register_message_handler(cmd_cancel, commands='cancel', state=Broadcast.waiting_for_input)
    dp.register_message_handler(broadcast_admin_msg, state=Broadcast.waiting_for_input)
