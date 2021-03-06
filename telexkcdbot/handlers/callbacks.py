import asyncio

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, InputFile, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from telexkcdbot.bot import bot
from telexkcdbot.config import IMG_DIR
from telexkcdbot.middlewares.localization import _, localization
from telexkcdbot.databases.users_db import users_db
from telexkcdbot.databases.comics_db import comics_db
from telexkcdbot.common_utils import send_comic
from telexkcdbot.keyboards import kboard
from telexkcdbot.comic_data_getter import comics_data_getter
from telexkcdbot.handlers.handlers_utils import (send_menu, send_bookmarks, remove_callback_kb,
                                                 calc_new_comic_id, flip_next, States, is_explained)


async def cb_select_lang(call: CallbackQuery, state: FSMContext):
    """Handles language buttons on /start command"""

    await States.waiting.set()  # Lock user input
    selected_lang = call.data[:2]
    await localization.set_user_locale(selected_lang)
    await users_db.set_user_lang(call.from_user.id, selected_lang)
    await call.message.delete()

    commands_list = [
        BotCommand(command="start", description=_("Start/restart bot + change language")),
        BotCommand(command="bookmarks", description=_("Show my bookmarks")),
        BotCommand(command="menu", description=_("Show menu"))
    ]
    await bot.set_my_commands(commands=commands_list)

    username = call.from_user.username
    hello_text = _("<b>❗ Hello, {}!").format(username) if username else _("<b>❗ Hello!")
    text = hello_text + _("\nI'm telexkcdbot — functional telegram bot "
                          "for convenient reading xkcd comics.\n"
                          "<i><a href='https://github.com/coryphoenixxx/telexkcdbot'>[Source code]</a></i></b>")
    await call.message.answer(text, disable_web_page_preview=True)

    await call.message.answer_photo(InputFile(IMG_DIR / 'bot_image.png'))

    await asyncio.sleep(2)
    await send_menu(call.from_user.id)
    await state.finish()  # Unlock user input


async def cb_menu(call: CallbackQuery, state: FSMContext):
    """Handles "Menu" button click"""

    await state.finish()
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
    await send_bookmarks(user_id=call.from_user.id,
                         message_id=call.message.message_id,
                         msg_text=call.message.text,
                         state=state,
                         keyboard=await kboard.menu(call.from_user.id))


async def cb_toggle_lang_btn(call: CallbackQuery):
    """Handles "Add/Remove 🇷🇺/🇬🇧 Button" button click"""

    await users_db.toggle_lang_btn_status(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_toggle_only_ru_mode_status(call: CallbackQuery):
    """Handles "Только переводы" button click for Russian users"""

    await users_db.toggle_only_ru_mode_status(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=await kboard.menu(call.from_user.id))


async def cb_admin_support(call: CallbackQuery):
    """Handles "Admin Support" button click"""

    await call.message.delete()
    await States.typing_msg_to_admin.set()
    await call.message.answer(text=_("❗ <b>Type and send a message (about bugs or suggestions, please). "
                                     "You can send a screenshot too.</b>"),
                              reply_markup=await kboard.menu_or_xkcding(call.from_user.id))


async def cb_start_xkcding(call: CallbackQuery, state: FSMContext):
    """Handles "Start xkcding" button click"""

    await state.finish()
    await call.message.delete() if '❗' in call.message.text else await remove_callback_kb(call)
    await send_comic(call.from_user.id, comic_id=1)


async def cb_continue_xkcding(call: CallbackQuery, state: FSMContext):
    """Handles "Continue xkcding" button click"""

    await state.finish()
    await call.message.delete() if '❗' in call.message.text else await remove_callback_kb(call)

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    await send_comic(call.from_user.id, comic_id=last_comic_id, comic_lang=last_comic_lang)


async def cb_navigation(call: CallbackQuery):
    """Handles "|<<, <Prev, Rand, Next>, >>|" buttons click"""

    await remove_callback_kb(call)
    action = call.data.split('_')[1]
    last_comic_id, _ = await users_db.get_last_comic_info(call.from_user.id)
    new_comic_id = await calc_new_comic_id(call.from_user.id, last_comic_id, action)
    await send_comic(call.from_user.id, comic_id=new_comic_id)


async def cb_toggle_comic_lang(call: CallbackQuery):
    """Handles "🇷🇺, 🇬🇧" buttons click under the comic"""

    await remove_callback_kb(call)

    new_comic_lang = call.data[-2:]
    last_comic_id, _ = await users_db.get_last_comic_info(call.from_user.id)

    keyboard = kboard.flipping if 'flip' in call.data else kboard.navigation

    await send_comic(call.from_user.id,
                     comic_id=last_comic_id,
                     keyboard=keyboard,
                     comic_lang=new_comic_lang,
                     from_toggle_lang_cb=True)


async def cb_explain(call: CallbackQuery, state: FSMContext,):
    """Handles "Explain" button click"""

    await States.waiting.set()  # Lock user input

    # Delete message if couldn't get explanation, else remove keyboard
    await call.message.delete() if '❗' in call.message.text else await call.message.edit_reply_markup()

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id, last_comic_lang)

    url = f"https://www.explainxkcd.com/{last_comic_id}"

    user_lang = await users_db.get_user_lang(call.from_user.id)
    if user_lang == 'ru':
        text = await comics_data_getter.get_ru_explanation(last_comic_id, url)
        text = f"<i>{text}...</i>\n\n<a href='{url}'><u>↪ [ПОЛНЫЙ ТЕКСТ]</u> 🇬🇧</a>"
    else:
        text = await comics_data_getter.get_explanation(last_comic_id, url)
        text = f"<i>{text}...</i>\n\n<a href='{url}'><u>↪ [FULL TEXT]</u></a>"

    keyboard = kboard.flipping if 'flip' in call.data else kboard.navigation
    keyboard = await keyboard(call.from_user.id, comic_data, last_comic_lang, is_explained=is_explained(text))

    await call.message.answer(text,
                              reply_markup=keyboard,
                              disable_web_page_preview=True,
                              disable_notification=True)

    await state.set_state()  # Unlock user input


async def cb_toggle_bookmark_status(call: CallbackQuery):
    """Handles "❤Bookmark", "💔Unbookmark" buttons click"""

    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(call.from_user.id)
    user_bookmarks_list = await users_db.get_bookmarks(call.from_user.id)

    if last_comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(last_comic_id)
    else:
        user_bookmarks_list.append(last_comic_id)

    await users_db.update_bookmarks(call.from_user.id, user_bookmarks_list)

    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)

    keyboard = kboard.flipping if 'flip' in call.data else kboard.navigation
    keyboard = await keyboard(call.from_user.id,
                              comic_data,
                              last_comic_lang,
                              is_explained=is_explained(call.message.text))

    await call.message.edit_reply_markup(reply_markup=keyboard)


async def cb_flip_next(call: CallbackQuery, state: FSMContext):
    """Handles "Forward>" button click in flipping mode"""

    await remove_callback_kb(call)
    await flip_next(call.from_user.id, state)


async def cb_flip_break(call: CallbackQuery, state: FSMContext):
    """Handles "↩Break" button click in flipping mode"""

    user_id = call.from_user.id
    last_comic_id, last_comic_lang = await users_db.get_last_comic_info(user_id)
    comic_data = await comics_db.get_comic_data_by_id(last_comic_id)

    keyboard = await kboard.navigation(user_id,
                                       comic_data,
                                       last_comic_lang,
                                       is_explained=is_explained(call.message.text))
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await state.reset_data()


def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(cb_select_lang,
                                       Text(endswith='user_lang'),
                                       state=[States.language_selection, None])
    dp.register_callback_query_handler(cb_menu, Text('menu'), state=[States.typing_msg_to_admin, None])
    dp.register_callback_query_handler(cb_toggle_notification_sound_status, Text(startswith='notification'))
    dp.register_callback_query_handler(cb_toggle_only_ru_mode_status, Text(startswith='only_ru_mode'))
    dp.register_callback_query_handler(cb_admin_support, Text('admin_support'))
    dp.register_callback_query_handler(cb_send_bookmarks, Text('user_bookmarks'))
    dp.register_callback_query_handler(cb_toggle_lang_btn, Text(('add_lang_btn', 'remove_lang_btn')))
    dp.register_callback_query_handler(cb_start_xkcding,
                                       Text('start_xkcding'),
                                       state=[States.typing_msg_to_admin, None])
    dp.register_callback_query_handler(cb_continue_xkcding,
                                       Text('continue_xkcding'),
                                       state=[States.typing_msg_to_admin, None])
    dp.register_callback_query_handler(cb_navigation, Text(startswith='nav_'))
    dp.register_callback_query_handler(cb_toggle_comic_lang, Text(('ru', 'flip_ru', 'en', 'flip_en')))
    dp.register_callback_query_handler(cb_explain, Text(('explain', 'flip_explain')))
    dp.register_callback_query_handler(cb_toggle_bookmark_status, Text(endswith='bookmark'))
    dp.register_callback_query_handler(cb_flip_next, Text('flip_next'))
    dp.register_callback_query_handler(cb_flip_break, Text('flip_break'))
