from random import randint

from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from contextlib import suppress

from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import send_comic
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.xkcd_parser import parser
from src.telexkcdbot.handlers.handlers_utils import (send_menu, send_bookmarks, remove_callback_kb,
                                                     trav_step, suppress_exceptions)


async def cb_menu(call: CallbackQuery, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await call.message.delete()

    await send_menu(call.from_user.id)


async def cb_toggle_subscription_status(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await call.message.edit_reply_markup() if 'MENU' in call.message.text else await call.message.delete()

    await users_db.toggle_subscription_status(call.from_user.id)
    inner_text = f"<u>{call.data}d</u> for" if call.data == 'subscribe' else f"<u>{call.data}d</u> from"
    await call.message.answer(f"❗ <b>You have been {inner_text} "
                              f"notification you whenever a new xkcd is released!</b>",
                              reply_markup=await kboard.menu(call.from_user.id))


async def cb_user_bookmarks(call: CallbackQuery, state: FSMContext):
    with suppress(*suppress_exceptions):
        await call.message.edit_reply_markup() if 'MENU' in call.message.text else await call.message.delete()
    await send_bookmarks(call.from_user.id,
                         state,
                         keyboard=await kboard.menu(call.from_user.id))


async def cb_toggle_lang_btn(call: CallbackQuery):
    action = call.data[:3]
    user_lang = 'ru' if action == 'add' else 'en'
    await users_db.set_user_lang(call.from_user.id, user_lang)

    with suppress(*suppress_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_start_xkcding(call: CallbackQuery):
    await remove_callback_kb(call)

    await send_comic(call.from_user.id, comic_id=1)


async def cb_continue_xkcding(call: CallbackQuery):
    await remove_callback_kb(call)

    comic_id, comic_lang = await users_db.get_cur_comic_info(call.from_user.id)
    await send_comic(call.from_user.id, comic_id=comic_id, comic_lang=comic_lang)


async def cb_navigation(call: CallbackQuery):
    await remove_callback_kb(call)

    comic_id, _ = await users_db.get_cur_comic_info(call.from_user.id)
    action = call.data.split('_')[1]
    latest = await comics_db.get_last_comic_id()

    actions = {
        'first': 1,
        'prev': comic_id - 1,
        'random': randint(1, latest),
        'next': comic_id + 1,
        'last': latest
    }

    new_comic_id = actions.get(action)

    if new_comic_id <= 0:
        new_comic_id = latest
    elif new_comic_id > latest:
        new_comic_id = 1

    await send_comic(call.from_user.id, comic_id=new_comic_id)


async def cb_toggle_comic_lang(call: CallbackQuery, keyboard=kboard.navigation):
    await remove_callback_kb(call)

    comic_id, _ = await users_db.get_cur_comic_info(call.from_user.id)
    new_comic_lang = call.data[-2:]

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await send_comic(call.from_user.id, comic_id=comic_id, keyboard=keyboard, comic_lang=new_comic_lang)


async def cb_explain(call: CallbackQuery, keyboard=kboard.navigation):
    await remove_callback_kb(call)

    comic_id, comic_lang = await users_db.get_cur_comic_info(call.from_user.id)

    text = await parser.get_explanation(comic_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal

    comic_data = await comics_db.get_comic_data_by_id(comic_id, comic_lang)

    await call.message.answer(text,
                              reply_markup=await keyboard(call.from_user.id, comic_data, comic_lang=comic_lang),
                              disable_web_page_preview=True)


async def cb_toggle_bookmark_status(call: CallbackQuery, keyboard=kboard.navigation):
    with suppress(*suppress_exceptions):
        await call.message.delete() if 'your bookmarks' in call.message.text else await call.message.edit_reply_markup()

    comic_id, comic_lang = await users_db.get_cur_comic_info(call.from_user.id)
    user_bookmarks_list = await users_db.get_bookmarks(call.from_user.id)

    if comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>added</u> to your bookmarks!</b>"

    await users_db.update_bookmarks(call.from_user.id, user_bookmarks_list)

    comic_data = await comics_db.get_comic_data_by_id(comic_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await call.message.answer(text, reply_markup=await keyboard(call.from_user.id, comic_data, comic_lang))


async def cb_trav_step(call: CallbackQuery, state: FSMContext):
    await remove_callback_kb(call)
    await trav_step(call.from_user.id, state)


async def cb_trav_stop(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)
    comic_data = await comics_db.get_comic_data_by_id(comic_id)
    with suppress(*suppress_exceptions):
        await call.message.edit_reply_markup(reply_markup=await kboard.navigation(user_id, comic_data, comic_lang))
    await state.reset_data()


def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(cb_menu, Text(equals='menu'))
    dp.register_callback_query_handler(cb_toggle_subscription_status, Text(endswith='subscribe'))
    dp.register_callback_query_handler(cb_user_bookmarks, Text('user_bookmarks'))
    dp.register_callback_query_handler(cb_toggle_lang_btn, Text(equals=('add_lang_btn', 'remove_lang_btn')))
    dp.register_callback_query_handler(cb_start_xkcding, Text('start_xkcding'))
    dp.register_callback_query_handler(cb_continue_xkcding, Text('continue_xkcding'))
    dp.register_callback_query_handler(cb_navigation, Text(startswith='nav_'))
    dp.register_callback_query_handler(cb_toggle_comic_lang, Text(equals=('ru', 'trav_ru', 'en', 'trav_en')))
    dp.register_callback_query_handler(cb_explain, Text(equals=('explain', 'trav_explain')))
    dp.register_callback_query_handler(cb_toggle_bookmark_status, Text(endswith='bookmark'))
    dp.register_callback_query_handler(cb_trav_step, Text('trav_step'))
    dp.register_callback_query_handler(cb_trav_stop, Text('trav_stop'))
