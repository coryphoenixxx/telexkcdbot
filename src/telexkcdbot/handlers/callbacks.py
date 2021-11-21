from typing import Callable

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.telexkcdbot.middlewares.localization import _, localization
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import send_comic
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.comic_data_getter import comic_data_getter
from src.telexkcdbot.handlers.handlers_utils import (send_menu, send_bookmarks, remove_callback_kb,
                                                     calc_new_comic_id, flip_next)
from src.telexkcdbot.config import IMG_DIR
from src.telexkcdbot.handlers.default import States


async def cb_select_lang(call: CallbackQuery, state: FSMContext):
    selected_lang = call.data[:2]
    await localization.set_user_locale(selected_lang)
    await users_db.set_user_lang(call.from_user.id, selected_lang)
    await call.message.delete()
    await state.finish()

    username = call.from_user.username
    if username:
        await call.message.answer(_("<b>❗ Hello, {}!\nThe telexkcdbot at your disposal!</b>".format(username)))
    else:
        await call.message.answer(_("<b>❗ Hello!\nThe telexkcdbot at your disposal!</b>"))

    await call.message.answer_photo(InputFile(IMG_DIR / 'bot_image.png'))
    await send_menu(call.from_user.id)


async def cb_menu(call: CallbackQuery, state: FSMContext):
    """Handles "Menu" button click"""

    await state.reset_data()
    await call.message.delete()
    await send_menu(call.from_user.id)


async def cb_toggle_notification_sound_status(call: CallbackQuery):
    """Handles "Enable/Disable notification sound" button click"""

    await users_db.toggle_notification_sound_status(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_send_bookmarks(call: CallbackQuery, state: FSMContext):
    """Handles "My Bookmarks" button click"""

    await remove_callback_kb(call)
    await send_bookmarks(call.from_user.id, state, keyboard=await kboard.menu(call.from_user.id))


async def cb_toggle_lang_btn(call: CallbackQuery):
    """Handles "Add/Remove 🇷🇺/🇬🇧 Button" button click"""

    await users_db.toggle_lang_btn_status(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_toggle_only_ru_mode_status(call: CallbackQuery):
    """Handles "Только переводы" button click for Russian users"""

    await users_db.toggle_only_ru_mode_status(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_start_xkcding(call: CallbackQuery):
    """Handles "Start xkcding" button click"""

    await remove_callback_kb(call)
    await send_comic(call.from_user.id, comic_id=1)


async def cb_continue_xkcding(call: CallbackQuery):
    """Handles "Continue xkcding" button click"""

    await remove_callback_kb(call)
    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    await send_comic(call.from_user.id, comic_id=last_comic_id, comic_lang=last_comic_lang)


async def cb_navigation(call: CallbackQuery):
    """Handles "|<<, <Prev, Rand, Next>, >>|" buttons click"""

    await remove_callback_kb(call)
    action = call.data.split('_')[1]
    last_comic_id, _ = await users_db.get_last_comic_info(call.from_user.id)
    new_comic_id = await calc_new_comic_id(call.from_user.id, last_comic_id, action)
    await send_comic(call.from_user.id, comic_id=new_comic_id)


async def cb_toggle_comic_lang(call: CallbackQuery, keyboard=kboard.navigation):
    """Handles "🇷🇺, 🇬🇧" buttons click under the comic"""

    await remove_callback_kb(call)
    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    new_comic_lang = call.data[-2:]

    if 'flip' in call.data:  # if we in flipping mode then change keyboard type
        keyboard = kboard.flipping
    await send_comic(call.from_user.id,
                     comic_id=last_comic_id,
                     keyboard=keyboard,
                     comic_lang=new_comic_lang,
                     from_toggle_lang_cb=True)


async def cb_explain(call: CallbackQuery, keyboard: Callable = kboard.navigation):
    """Handles "Explain" button click"""

    if '[FULL TEXT]' in call.message.text:
        await call.message.delete()  # delete explain text if it exists
    else:
        await call.message.edit_reply_markup()  # else remove keyboard

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    text = await comic_data_getter.get_explanation(last_comic_id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id, last_comic_lang)

    if 'flip' in call.data:  # if we in flipping mode then change keyboard type
        keyboard = kboard.flipping
    await call.message.answer(text,
                              reply_markup=await keyboard(call.from_user.id, comic_data, last_comic_lang),
                              disable_web_page_preview=True,
                              disable_notification=True)


async def cb_toggle_bookmark_status(call: CallbackQuery, keyboard=kboard.navigation):
    """Handles "❤Bookmark, 💔Unbookmark" buttons click"""

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    user_bookmarks_list = await users_db.get_bookmarks(call.from_user.id)

    user_bookmarks_list.remove(last_comic_id) if last_comic_id in user_bookmarks_list \
        else user_bookmarks_list.append(last_comic_id)

    await users_db.update_bookmarks(call.from_user.id, user_bookmarks_list)

    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)

    if 'flip' in call.data:  # if we in flipping mode then change keyboard type
        keyboard = kboard.flipping
    await call.message.edit_reply_markup(reply_markup=await keyboard(call.from_user.id, comic_data, last_comic_lang))


async def cb_flip_next(call: CallbackQuery, state: FSMContext):
    """Handles "Next>" button click in flipping mode"""

    await remove_callback_kb(call)
    await flip_next(call.from_user.id, state)


async def cb_flip_break(call: CallbackQuery, state: FSMContext):
    """Handles "Break" button click in flipping mode"""

    user_id = call.from_user.id
    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(user_id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)
    await call.message.edit_reply_markup(reply_markup=await kboard.navigation(user_id, comic_data, last_comic_lang))
    await state.reset_data()


def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(cb_select_lang, Text(endswith='user_lang'), state=[States.choose_lang, None])
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
