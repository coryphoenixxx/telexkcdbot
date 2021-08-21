from random import randint

from contextlib import suppress

from aiogram.types import CallbackQuery
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from funcs import *

storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)

"""ENTRY POINT"""


@dp.message_handler(CommandStart())
@rate_limit(2)
async def start(msg: Message, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await users_db.add_user(msg.from_user.id)
    await msg.answer(f"<b>❗Hey!    [¬º-°]¬\nThe <u>{(await bot.me).username}</u> at your disposal!</b>")
    await msg.answer_photo(InputFile('static/bot_image.png'))
    await asyncio.sleep(3)
    await show_menu(msg, state)


"""MENU"""


async def send_menu(user_id):
    help_text = """<b>*** MENU ***</b>

Type in the <u><b>number</b></u> and I'll find a comic with this number!
Type in the <u><b>word</b></u> and I'll find comics, which contains this word! 


<u><b>In menu you can:</b></u>
— subscribe for the new comic release <i>(every Mon, Wed and Fri USA time)</i>.
— read comics from your bookmarks.
— remove language button <i>(under the comic, which have russian translation)</i> if you don't need it.
— start xkcding!


❗❗❗
If something goes wrong or looks strange try to view a comic in your browser <i>(I'll give you a link)</i>."""

    await bot.send_message(user_id, help_text, reply_markup=await kboard.menu(user_id))


@dp.message_handler(commands=['menu', 'help'])
@rate_limit(2)
async def show_menu(msg: Message, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await send_menu(msg.from_user.id)


@dp.callback_query_handler(Text(equals='menu'))
async def show_menu(call: CallbackQuery, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id)

    await send_menu(call.from_user.id)


@dp.callback_query_handler(Text(endswith='subscribe'))
async def subscriber(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        if 'MENU' in call.message.text:
            await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.delete_message(call.from_user.id, message_id=call.message.message_id)

    await users_db.change_subscription_status(call.from_user.id)
    inner_text = f"<u>{call.data}d</u> for" if call.data == 'subscribe' else f"<u>{call.data}d</u> from"
    await call.message.answer(f"❗ <b>You have been {inner_text} "
                              f"notification you whenever a new xkcd is released!</b>",
                              reply_markup=await kboard.menu(call.from_user.id))


async def show_bookmarks(user_id, message_id, state, keyboard=None):
    bookmarks_list = await users_db.get_bookmarks(user_id)
    _len = len(bookmarks_list)

    if not _len:
        text = f"❗ <b>You have no bookmarks. You can bookmark a comic with the ❤ press.</b>"
        if keyboard:
            await bot.send_message(user_id, text, reply_markup=keyboard)
        else:
            await bot.send_message(user_id, text, reply_markup=await kboard.menu_or_xkcding(user_id))

    else:
        await bot.send_message(user_id, f"❗ <b>You have <u><b>{_len}</b></u> bookmarks</b>:")

        comics_ids, titles = [], []
        for comic_id in bookmarks_list:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            comics_ids.append(comic_data[0])
            titles.append(comic_data[1])

        await send_comics_list_text_in_bunches(user_id, comics_ids, titles)

        await state.update_data(list=bookmarks_list)
        await trav_step(user_id, message_id, state)


@dp.callback_query_handler(Text('user_bookmarks'))
async def call_show_bookmarks(call: CallbackQuery, state: FSMContext):
    if 'MENU' in call.message.text:
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)
    else:
        await bot.delete_message(call.from_user.id, message_id=call.message.message_id)
    await show_bookmarks(call.from_user.id,
                         call.message.message_id,
                         state,
                         keyboard=await kboard.menu(call.from_user.id))


@dp.message_handler(commands=['bookmarks'])
async def msg_show_bookmarks(msg: Message, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)
    await show_bookmarks(msg.from_user.id, msg.message_id, state)


@dp.callback_query_handler(Text(equals=('add_lang_btn', 'remove_lang_btn')))
async def set_ru_button(call: CallbackQuery):
    action = call.data[:3]
    user_lang = 'ru' if action == 'add' else 'en'
    await users_db.set_user_lang(call.from_user.id, user_lang)

    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id,
                                            message_id=call.message.message_id,
                                            reply_markup=await kboard.menu(call.from_user.id))


@dp.callback_query_handler(Text('start_xkcding'))
async def start_xkcding(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    comic_data = await comics_db.get_comic_data_by_id(1)
    await send_comic(call.from_user.id, data=comic_data)


async def continue_xkcding(user_id):
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)

    if comic_id == 0:
        comic_id = 1

    if comic_lang == 'ru':
        comic_data = await comics_db.get_ru_comic_data_by_id(comic_id)
    else:
        comic_data = await comics_db.get_comic_data_by_id(comic_id)

    await send_comic(user_id, data=comic_data, comic_lang=comic_lang)


@dp.callback_query_handler(Text('continue_xkcding'))
async def call_continue_xkcding(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    await continue_xkcding(call.from_user.id)


"""MAIN"""


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

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
    if new_comic_id > latest:
        new_comic_id = 1

    comic_data = await comics_db.get_comic_data_by_id(new_comic_id)
    await send_comic(call.from_user.id, data=comic_data)


@dp.callback_query_handler(Text(equals=('ru', 'trav_ru', 'en', 'trav_en')))
async def ru_version(call: CallbackQuery, keyboard=kboard.navigation):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    comic_id, _ = await users_db.get_cur_comic_info(call.from_user.id)

    if 'en' in call.data:
        comic_lang = 'en'
        comic_data = await comics_db.get_comic_data_by_id(comic_id)
    else:
        comic_lang = 'ru'
        comic_data = await comics_db.get_ru_comic_data_by_id(comic_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await send_comic(call.from_user.id, data=comic_data, keyboard=keyboard, comic_lang=comic_lang)


@dp.callback_query_handler(Text(equals=('explain', 'trav_explain')))
async def explanation(call: CallbackQuery, keyboard=kboard.navigation):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    comic_id, comic_lang = await users_db.get_cur_comic_info(call.from_user.id)

    text = await parser.get_explanation(comic_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await call.message.answer(text,
                              reply_markup=await keyboard(call.from_user.id, comic_id, comic_lang=comic_lang),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text(endswith='bookmark'))
async def bookmark(call: CallbackQuery, keyboard=kboard.navigation):
    comic_id, comic_lang = await users_db.get_cur_comic_info(call.from_user.id)
    user_bookmarks_list = await users_db.get_bookmarks(call.from_user.id)

    if comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>added</u> to your bookmarks!</b>"

    await users_db.update_bookmarks(call.from_user.id, user_bookmarks_list)

    with suppress(*suppress_exceptions):
        if 'your bookmarks' in call.message.text:
            await bot.delete_message(call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await call.message.answer(text, reply_markup=await keyboard(call.from_user.id, comic_id, comic_lang=comic_lang))


"""TRAVERSAL"""


async def trav_step(user_id: int, message_id: int, state: FSMContext):
    list_ = (await state.get_data()).get('list')

    if not list_:
        await trav_stop(user_id, message_id, state)
    else:
        lang = (await state.get_data()).get('lang')
        if not lang:
            comic_lang = 'en'
            comic_data = await comics_db.get_comic_data_by_id(list_.pop(0))
        else:
            comic_lang = 'ru'
            comic_data = await comics_db.get_ru_comic_data_by_id(list_.pop(0))

        if list_:
            await send_comic(user_id, data=comic_data, keyboard=kboard.traversal, comic_lang=comic_lang)
            await state.update_data(list=list_)
        else:
            await send_comic(user_id, data=comic_data, keyboard=kboard.navigation, comic_lang=comic_lang)
            await state.reset_data()


@dp.callback_query_handler(Text('trav_step'))
async def call_trav_step(call: CallbackQuery, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)
    await trav_step(call.from_user.id, call.message.message_id, state)


async def trav_stop(user_id: int, message_id: int, state: FSMContext):
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(user_id,
                                            message_id=message_id,
                                            reply_markup=await kboard.navigation(user_id,
                                                                                 comic_id,
                                                                                 comic_lang))
    await state.reset_data()


@dp.callback_query_handler(Text('trav_stop'))
async def call_trav_stop(call: CallbackQuery, state: FSMContext):
    await trav_stop(call.from_user.id, call.message.message_id, state)


"""ADMIN'S"""


@dp.message_handler(commands='admin')
@admin
async def admin(msg: Message, state: FSMContext):
    await state.reset_data()
    await msg.answer('<b>*** ADMIN PANEL ***</b>',
                     reply_markup=await kboard.admin_panel())


@dp.callback_query_handler(Text('change_spec_status'))
async def change_spec_status(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.delete_message(call.from_user.id, message_id=call.message.message_id)

    cur_comic_id, _ = await users_db.get_cur_comic_info(ADMIN_ID)
    await comics_db.change_spec_status(cur_comic_id)
    await call.message.answer(text=f"<b>*** ADMIN PANEL ***</b>\n❗ <b>It's done for {cur_comic_id}</b>",
                              reply_markup=await kboard.admin_panel())


@dp.callback_query_handler(Text(startswith='send_'))
async def send_log(call: CallbackQuery):
    filename = './logs/actions.log' if 'actions' in call.data else './logs/errors.log'

    try:
        await call.message.answer_document(InputFile(filename))
    except BadRequest as err:
        logger.error(err)


@dp.callback_query_handler(Text('users_info'))
async def users_info(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.delete_message(call.from_user.id, message_id=call.message.message_id)

    all_users_num = len(await users_db.get_all_users_ids())
    subscribed_users_num = len(await users_db.get_subscribed_users())
    active_users_num = await users_db.get_last_month_active_users_num()
    text = f"""<b>*** ADMIN PANEL ***</b>
❗ <b>Total</b>: <i>{all_users_num}</i>
        <b>Subs</b>: <i>{subscribed_users_num}</i>
        <b>Active</b>: <i>{active_users_num}</i>"""
    await call.message.answer(text,
                              reply_markup=await kboard.admin_panel())


class Broadcast(StatesGroup):
    waiting_for_input = State()


@dp.callback_query_handler(Text('broadcast'))
async def type_broadcast_message(call: CallbackQuery):
    await Broadcast.waiting_for_input.set()
    await call.message.answer(text='❗ <b>Type in a broadcast message (or /cancel):</b>')


@dp.message_handler(state=Broadcast.waiting_for_input, commands='cancel')
async def cancel_handler(msg: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        return

    await msg.answer(text='❗ <b>Canceled.</b>')
    await state.finish()


@dp.message_handler(state=Broadcast.waiting_for_input)
async def send_broadcast_admin_message(msg: Message, state: FSMContext):
    text = f'❗❗❗ <b>ADMIN MESSAGE:\n</b>  {msg.text}'
    all_users_ids = await users_db.get_all_users_ids()
    await broadcast(all_users_ids, text=text)
    await state.finish()


"""TYPING"""


@dp.message_handler()
@rate_limit(1)
async def typing(msg: Message, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)
    await state.reset_data()

    user_input = msg.text

    if user_input.isdigit():
        comic_id = int(user_input)
        latest = await comics_db.get_last_comic_id()

        if (comic_id > latest) or (comic_id <= 0):
            await msg.reply(f"❗❗❗\n<b>Please, enter a number between 1 and {latest}!</b>",
                            reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await send_comic(msg.from_user.id, data=comic_data)
    else:
        user_input = await preprocess_text(user_input)
        is_cyr = await is_cyrillic(user_input)

        if len(user_input) < 2:
            await msg.reply(f"❗ <b>I think there's no necessity to search by one character!)</b>")
        else:
            found_comics_list = await comics_db.get_comics_info_by_title(user_input)

            if not found_comics_list or not user_input:
                await msg.reply(f"❗❗❗\n<b>There's no such comic title or command!</b>",
                                reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
            else:
                comic_lang = 'en'
                if is_cyr:
                    comic_lang = 'ru'
                    await state.update_data(lang='ru')

                found_comics_num = len(found_comics_list[0])

                if found_comics_num == 1:
                    await msg.reply(f"❗ <b>I found one:</b>")
                    comic_id = found_comics_list[0][0]

                    if is_cyr:
                        comic_data = await comics_db.get_ru_comic_data_by_id(comic_id)
                    else:
                        comic_data = await comics_db.get_comic_data_by_id(comic_id)
                    await send_comic(msg.from_user.id, data=comic_data, comic_lang=comic_lang)

                elif found_comics_num >= 2:
                    comics_ids, comics_titles, ru_comics_titles = found_comics_list

                    await msg.reply(f"❗ <b>I found <u><b>{found_comics_num}</b></u> comics:</b>")

                    titles = ru_comics_titles if is_cyr else comics_titles

                    await send_comics_list_text_in_bunches(msg.from_user.id, comics_ids, titles, comic_lang)

                    await state.update_data(list=list(comics_ids))
                    await trav_step(msg.from_user.id, msg.message_id, state)
