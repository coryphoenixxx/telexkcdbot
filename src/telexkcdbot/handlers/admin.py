from contextlib import suppress

from loguru import logger

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.telexkcdbot.bot import bot
from src.telexkcdbot.keyboards import kboard, support_cb_data
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import broadcast, suppressed_exceptions, remove_prev_message_kb
from src.telexkcdbot.handlers.handlers_utils import States, send_menu
from src.telexkcdbot.config import ADMIN_ID, LOGS_DIR
from src.telexkcdbot.middlewares.localization import _


admin_panel_text_base = "<b>*** ADMIN PANEL ***</b>\n"


async def cmd_admin(msg: Message, state: FSMContext):
    if msg.from_user.id != int(ADMIN_ID):
        await msg.answer("❗ <b>For admin only!</b>")
    else:
        await remove_prev_message_kb(msg)
        await state.reset_data()

        await msg.answer(admin_panel_text_base,
                         reply_markup=await kboard.admin_panel())


async def cb_users_info(call: CallbackQuery):
    with suppress(*suppressed_exceptions):
        await call.message.delete()

    users_info = await users_db.get_admin_users_info()

    await call.message.answer(text=f"{admin_panel_text_base}"
                                   f"<b>Total</b>: <i>{users_info.users_num}</i>\n"
                                   f"<b>Active</b>: <i>{users_info.last_week_active_users_num}</i>\n"
                                   f"<b>In only-ru mode: </b>: <i>{users_info.only_ru_users_num}</i>\n",
                              reply_markup=await kboard.admin_panel())


async def cb_toggle_spec_status(call: CallbackQuery):
    last_comic_id, _ = await users_db.get_last_comic_info(ADMIN_ID)
    await comics_db.toggle_spec_status(last_comic_id)
    await call.message.edit_text(text=f"{admin_panel_text_base}❗ <b>It's done for {last_comic_id}.</b>",
                                 reply_markup=await kboard.admin_panel())


async def cb_send_log(call: CallbackQuery):
    filename = LOGS_DIR / 'actions.log' if 'actions' in call.data else LOGS_DIR / 'errors.log'

    try:
        await call.message.answer_document(InputFile(filename))
    except BadRequest as err:
        logger.error(f"Couldn't send logs ({err})")


async def cb_type_broadcast_message(call: CallbackQuery):
    await States.typing_broadcast_msg.set()
    await call.message.answer("❗ <b>Type in a broadcast message (or /cancel):</b>")


async def cmd_cancel(msg: Message, state: FSMContext):
    if await state.get_state() is None:
        return

    await msg.answer("❗ <b>Canceled.</b>")
    await state.finish()


async def broadcast_admin_msg(msg: Message, state: FSMContext):
    await broadcast(text=_(f"❗ <u><b>ADMIN MESSAGE:</b></u>\n{msg.text}"))
    await state.finish()


async def user_support_msg(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    await bot.delete_message(user_id, msg.message_id - 1)

    is_banned = await users_db.get_ban_status(user_id)
    if not is_banned:
        username = msg.from_user.username
        message_id = msg.message_id
        await bot.send_message(ADMIN_ID,
                               text=f"❗ <b>New message from user\n"
                                    f"({user_id} | {username} | {msg.from_user.language_code})</b>")
        await msg.copy_to(ADMIN_ID, reply_markup=await kboard.support_keyboard(user_id, message_id))
    await state.finish()
    await send_menu(user_id)


async def cb_answer(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await States.typing_admin_support_msg.set()
    _, _, user_id, message_id = callback_data.values()
    await state.set_data(data={'user_id': user_id, 'message_id': message_id})
    await call.message.delete()


async def cb_ban(call: CallbackQuery, callback_data: dict):
    user_id = int(callback_data.get('user_id'))
    await users_db.ban_user(user_id)
    await call.message.delete()


async def admin_support_msg(msg: Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(data['user_id'], text=msg.text, reply_to_message_id=data['message_id'])
    await state.finish()


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands='admin')
    dp.register_callback_query_handler(cb_users_info, text='users_info')
    dp.register_callback_query_handler(cb_toggle_spec_status, text='change_spec_status')
    dp.register_callback_query_handler(cb_send_log, Text(startswith='send_'))
    dp.register_callback_query_handler(cb_type_broadcast_message, text='broadcast_admin_msg')
    dp.register_message_handler(cmd_cancel, commands='cancel', state=States.typing_broadcast_msg)
    dp.register_message_handler(broadcast_admin_msg, state=States.typing_broadcast_msg)
    dp.register_message_handler(user_support_msg,
                                state=States.typing_msg_to_admin,
                                content_types=['text', 'photo'])
    dp.register_message_handler(admin_support_msg,
                                state=States.typing_admin_support_msg)
    dp.register_callback_query_handler(cb_answer, support_cb_data.filter(type='answer'))
    dp.register_callback_query_handler(cb_ban, support_cb_data.filter(type='ban'))
