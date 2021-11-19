from contextlib import suppress

from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import send_comic
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.comic_data_getter import comic_data_getter
from src.telexkcdbot.handlers.handlers_utils import (send_menu, send_bookmarks, remove_callback_kb, calc_new_comic_id,
                                                     flip_next, suppressed_exceptions, remove_explain_or_bot_msg)


async def cb_menu(call: CallbackQuery, state: FSMContext):
    await state.reset_data()
    with suppress(*suppressed_exceptions):
        await call.message.delete()

    await send_menu(call.from_user.id)


async def cb_toggle_notification_sound_status(call: CallbackQuery):
    await users_db.toggle_notification_sound_status(call.from_user.id)

    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_send_bookmarks(call: CallbackQuery, state: FSMContext):
    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup() if 'MENU' in call.message.text else await call.message.delete()

    await send_bookmarks(call.from_user.id, state, keyboard=await kboard.menu(call.from_user.id))


async def cb_toggle_lang_btn(call: CallbackQuery):
    await users_db.toggle_lang_btn_status(call.from_user.id)

    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_toggle_only_ru_mode_status(call: CallbackQuery):
    await users_db.toggle_only_ru_mode_status(call.from_user.id)

    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_start_xkcding(call: CallbackQuery):
    await remove_callback_kb(call)

    await send_comic(call.from_user.id, comic_id=1)


async def cb_continue_xkcding(call: CallbackQuery):
    await remove_callback_kb(call)

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    await send_comic(call.from_user.id, comic_id=last_comic_id, comic_lang=last_comic_lang)


async def cb_navigation(call: CallbackQuery):
    await remove_callback_kb(call)

    action = call.data.split('_')[1]
    last_comic_id, _ = await users_db.get_last_comic_info(call.from_user.id)
    new_comic_id = await calc_new_comic_id(call.from_user.id, last_comic_id, action)
    await send_comic(call.from_user.id, comic_id=new_comic_id)


async def cb_toggle_comic_lang(call: CallbackQuery, keyboard=kboard.navigation):
    await remove_callback_kb(call)

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    new_comic_lang = call.data[-2:]

    if 'flip' in call.data:
        keyboard = kboard.flipping
    await send_comic(call.from_user.id, comic_id=last_comic_id, keyboard=keyboard, comic_lang=new_comic_lang, from_toggle_lang_cb=True)


async def cb_explain(call: CallbackQuery, keyboard=kboard.navigation):
    await remove_explain_or_bot_msg(call)

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    text = await comic_data_getter.get_explanation(last_comic_id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id, last_comic_lang)

    if 'flip' in call.data:
        keyboard = kboard.flipping
    await call.message.answer(text,
                              reply_markup=await keyboard(call.from_user.id, comic_data, last_comic_lang),
                              disable_web_page_preview=True,
                              disable_notification=True)


async def cb_toggle_bookmark_status(call: CallbackQuery, keyboard=kboard.navigation):
    await remove_explain_or_bot_msg(call)

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    user_bookmarks_list = await users_db.get_bookmarks(call.from_user.id)

    if last_comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(last_comic_id)
        text = f"❗ <b>Comic №{last_comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(last_comic_id)
        text = f"❗ <b>Comic №{last_comic_id} has been <u>added</u> to your bookmarks!</b>"

    await users_db.update_bookmarks(call.from_user.id, user_bookmarks_list)

    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)

    if 'flip' in call.data:
        keyboard = kboard.flipping
    await call.message.answer(text, reply_markup=await keyboard(call.from_user.id, comic_data, last_comic_lang))


async def cb_flip_next(call: CallbackQuery, state: FSMContext):
    await remove_callback_kb(call)
    await flip_next(call.from_user.id, state)


async def cb_flip_break(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(user_id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)
    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.navigation(user_id, comic_data, last_comic_lang))
    await state.reset_data()


def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(cb_menu, Text(equals='menu'))
    dp.register_callback_query_handler(cb_toggle_notification_sound_status, Text(startswith='notification'))
    dp.register_callback_query_handler(cb_toggle_only_ru_mode_status, Text(startswith='only_ru_mode'))
    dp.register_callback_query_handler(cb_send_bookmarks, Text('user_bookmarks'))
    dp.register_callback_query_handler(cb_toggle_lang_btn, Text(equals=('add_lang_btn', 'remove_lang_btn')))
    dp.register_callback_query_handler(cb_start_xkcding, Text('start_xkcding'))
    dp.register_callback_query_handler(cb_continue_xkcding, Text('continue_xkcding'))
    dp.register_callback_query_handler(cb_navigation, Text(startswith='nav_'))
    dp.register_callback_query_handler(cb_toggle_comic_lang, Text(equals=('ru', 'flip_ru', 'en', 'flip_en')))
    dp.register_callback_query_handler(cb_explain, Text(equals=('explain', 'flip_explain')))
    dp.register_callback_query_handler(cb_toggle_bookmark_status, Text(endswith='bookmark'))
    dp.register_callback_query_handler(cb_flip_next, Text('flip_next'))
    dp.register_callback_query_handler(cb_flip_break, Text('flip_break'))
