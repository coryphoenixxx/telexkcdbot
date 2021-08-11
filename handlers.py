import asyncio

from random import randint
from contextlib import suppress

from aiogram.types import Message, CallbackQuery, InputFile
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked, \
    UserDeactivated, MessageToEditNotFound, ChatNotFound, MessageCantBeEdited
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import comics_db, users_db, bot, loop, logger, preprocess_text, rate_limit, admin, is_cyrillic
from keyboard import kboard
from xkcd_parser import parser
from config import ADMIN_ID


storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)

suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


async def send_comic(user_id: int, data: dict, keyboard=kboard.navigation, comic_lang: str = 'en'):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data.values()

    await users_db.update_cur_comic_info(user_id, comic_id, comic_lang)

    link = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '')

    await bot.send_message(user_id, headline, disable_web_page_preview=True)

    if is_specific:
        await asyncio.sleep(0.05)
        await bot.send_message(user_id,
                               text=f"❗❗❗ It's a peculiar comic! It's preferable to view it "
                                    f"in <a href='{link}'>your browser</a>.",
                               disable_web_page_preview=True,
                               disable_notification=True)

    await asyncio.sleep(0.05)
    try:
        if img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, img_url, disable_notification=True)
        else:
            await bot.send_photo(user_id, InputFile('static/no_image.png'), disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest) as err:
        await bot.send_message(user_id,
                               text=f"❗❗❗ Can't get image, try it in your browser!",
                               disable_web_page_preview=True,
                               disable_notification=True)
        logger.error(f"Cant't send {comic_id} to {user_id} comic!", err)

    await asyncio.sleep(0.05)
    await bot.send_message(user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id, comic_lang),
                           disable_web_page_preview=True,
                           disable_notification=True)


"""ENTRY POINT"""


@dp.message_handler(CommandStart())
@rate_limit(5)
async def start(msg: Message):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)
    user_id = msg.from_user.id
    await users_db.add_user(user_id)
    bot_name = (await bot.me).username
    await msg.answer(f"Hey! The <b>{bot_name}</b> at your disposal!\t\t\t<b>[¬º-°]¬</b>")
    await msg.answer_photo(InputFile('static/bot_image.png'))
    await show_menu(msg)


"""MENU"""


@dp.message_handler(commands=['menu', 'help'])
@rate_limit(5)
async def show_menu(msg: Message):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)
    help_text = """
<b>*** MENU ***</b>

Type in the <u><b>comic number</b></u> and I'll find it for you!
Type in the <u><b>comic title</b></u> and I'll try to find it for you!


<u><b>In menu you can:</b></u>
— subscribe for a new comic.
— read comics from your bookmarks.
— remove language button <i>(under the comic, which have russian translation)</i> if you don't need it.
— start xkcding!


❗❗❗

If something goes wrong or looks strange try to view a comic in your browser <i>(I'll give you a link)</i>.
"""
    await msg.answer(help_text, reply_markup=await kboard.menu(msg.from_user.id))


@dp.callback_query_handler(Text(endswith='subscribe'))
async def subscriber(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        if 'subscribed' in call.message.text:
            await bot.delete_message(call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    user_id = call.from_user.id
    await users_db.subscribe(user_id) if call.data == 'subscribe' else await users_db.unsubscribe(user_id)

    inner_text = f"{call.data}d for" if call.data == 'subscribe' else f"{call.data}d from"
    await call.message.answer(f"❗ <b>You have been {inner_text} notification you whenever a new xkcd is released!</b>",
                              reply_markup=await kboard.menu(user_id))


@dp.callback_query_handler(Text('user_bookmarks'))
async def show_bookmarks(call: CallbackQuery, state: FSMContext):
    bookmarks_list = await users_db.get_bookmarks(call.from_user.id)
    len_ = len(bookmarks_list)
    if not len_:
        await call.message.answer(f"❗ <b>You've no bookmarks.</b>")
    else:
        await call.message.answer(f"❗ <b>You've <u><b>{len_}</b></u> bookmarks.</b>")
        await state.update_data(list=bookmarks_list)
        await trav_step(call, state)


@dp.callback_query_handler(Text(equals=('add_ru', 'remove_ru')))
async def set_ru_button(call: CallbackQuery):
    action = call.data[:-3]
    lang = 'ru' if action == 'add' else 'en'
    await users_db.set_user_lang(call.from_user.id, lang)
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


@dp.callback_query_handler(Text('continue_xkcding'))
async def continue_xkcding(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)
    comic_id, _ = await users_db.get_cur_comic_info(call.from_user.id)
    comic_data = await comics_db.get_comic_data_by_id(comic_id)
    await send_comic(call.from_user.id, data=comic_data)


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

    user_id = call.from_user.id
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)

    text, url = await parser.get_explanation(comic_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await call.message.answer(text,
                              reply_markup=await keyboard(user_id, comic_id, comic_lang=comic_lang),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text(endswith='bookmark'))
async def bookmark(call: CallbackQuery, keyboard=kboard.navigation):
    user_id = call.from_user.id
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)
    user_bookmarks_list = await users_db.get_bookmarks(user_id)

    if comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(comic_id)
        text = f"❗ <b>Comic №{comic_id} has been <u>added</u> to your bookmarks!</b>"

    await users_db.update_bookmarks(user_id, user_bookmarks_list)

    with suppress(*suppress_exceptions):
        if 'your bookmarks' in call.message.text:
            await bot.delete_message(call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    if 'trav' in call.data:
        keyboard = kboard.traversal
    await call.message.answer(text, reply_markup=await keyboard(user_id, comic_id, comic_lang=comic_lang))


"""TRAVERSAL"""


@dp.callback_query_handler(Text('trav_stop'))
async def trav_stop(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(user_id,
                                            message_id=call.message.message_id,
                                            reply_markup=await kboard.navigation(user_id, comic_id, comic_lang))
    await state.reset_data()


@dp.callback_query_handler(Text('trav_step'))
async def trav_step(call: (CallbackQuery, Message), state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(call.from_user.id, message_id=call.message.message_id)

    try:
        list_ = (await state.get_data())['list']
    except KeyError:
        await trav_stop(call, state)
    else:
        try:
            (await state.get_data())['lang']
        except KeyError:
            comic_data = await comics_db.get_comic_data_by_id(list_.pop(0))
            comic_lang = 'en'
        else:
            comic_data = await comics_db.get_ru_comic_data_by_id(list_.pop(0))
            comic_lang = 'ru'
        finally:
            await state.update_data(list=list_)

        if list_:
            await send_comic(call.from_user.id, data=comic_data, keyboard=kboard.traversal, comic_lang=comic_lang)
        else:
            await send_comic(call.from_user.id, data=comic_data, keyboard=kboard.navigation, comic_lang=comic_lang)
            await state.reset_data()


"""ADMIN'S"""


@dp.message_handler(commands='admin')
@admin
async def admin_panel(msg: Message):
    await bot.send_message(ADMIN_ID, '<b>*** ADMIN PANEL ***</b>', reply_markup=await kboard.admin_panel())


@dp.callback_query_handler(Text('full_test'))
async def full_test(call: CallbackQuery):
    latest = await comics_db.get_last_comic_id()
    for comic_id in range(1, latest + 1):
        try:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await send_comic(ADMIN_ID, data=comic_data)
            await asyncio.sleep(1)

            if comic_id in parser.real_ru_ids:
                comic_data = await comics_db.get_ru_comic_data_by_id(comic_id)
                await send_comic(ADMIN_ID, data=comic_data)
                await asyncio.sleep(1)
            text, url = await parser.get_explanation(comic_id)
            await call.message.answer(text,
                                      reply_markup=await kboard.navigation(ADMIN_ID, comic_id),
                                      disable_web_page_preview=True)

            await asyncio.sleep(3)
        except Exception as err:
            logger.error(f"Error with {comic_id}: {err}")
            await asyncio.sleep(601)  # telegram blocks bot for 10 min for flooding


@dp.callback_query_handler(Text('change_spec_status'))
async def change_spec_status(call: CallbackQuery):
    cur_comic_id, _ = await users_db.get_cur_comic_info(ADMIN_ID)
    await comics_db.change_spec_status(cur_comic_id)
    with suppress(*suppress_exceptions):
        await bot.send_message(ADMIN_ID, text=f"❗ <b>It's done for {cur_comic_id}, Your Mightiness!</b>")


@dp.callback_query_handler(Text(startswith='send_'))
async def send_log(call: CallbackQuery):
    if call.data == 'send_users_db':
        filename = './databases/users.db'
    else:
        filename = 'actions.log' if 'actions' in call.data else 'errors.log'

    try:
        await bot.send_document(ADMIN_ID, InputFile(filename))
    except BadRequest as err:
        logger.error(err)


@dp.callback_query_handler(Text('users_info'))
async def users_info(call: CallbackQuery):
    all_users_num = await users_db.length
    active_users_num = await users_db.get_last_month_active_users()
    with suppress(*suppress_exceptions):
        await bot.send_message(ADMIN_ID,
                               text=f"❗ <b>We already have {all_users_num} users caught in our net, Your Grace!\n"
                                    f"And {active_users_num} were active in the last month!</b>")


class Broadcast(StatesGroup):
    waiting_for_input = State()


@dp.callback_query_handler(Text('broadcast'))
async def broadcast(call: CallbackQuery):
    await Broadcast.waiting_for_input.set()
    await bot.send_message(ADMIN_ID, text='❗ <b>Type in a broadcast message (or /cancel):</b>')


@dp.message_handler(state=Broadcast.waiting_for_input, commands='cancel')
async def cancel_handler(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await bot.send_message(ADMIN_ID, text='❗ <b>Canceled.</b>.')
    await state.finish()


@dp.message_handler(state=Broadcast.waiting_for_input)
async def process_broadcast_message(msg: Message, state: FSMContext):
    count = 0
    for user_id in (await users_db.get_all_users_ids()):
        try:
            await bot.send_message(user_id, text=f'❗❗❗ <b>ADMIN MESSAGE:</b>  {msg.text}')
            count += 1
            if count % 20 == 0:
                await asyncio.sleep(1)
        except (BotBlocked, UserDeactivated, ChatNotFound):
            await users_db.delete_user(user_id)
            continue

    await bot.send_message(ADMIN_ID, f"❗ <b>Sent the broadcast message to {count} users!</b>")
    await state.finish()


"""TYPING"""


@dp.message_handler()
@rate_limit(2)
async def typing(msg: Message, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await state.reset_data()

    user_input = msg.text

    if user_input.isdigit():
        comic_id = int(user_input)
        latest = await comics_db.get_last_comic_id()
        if (comic_id > latest) or (comic_id <= 0):
            await msg.reply(f"❗❗❗ <b>Please, enter a number between 1 and {latest}!</b>")
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await send_comic(msg.from_user.id, data=comic_data)
    else:
        user_input = await preprocess_text(user_input)
        found_comics_list = await comics_db.get_comics_ids_by_title(user_input)
        if not found_comics_list or not user_input:
            await msg.reply(f"❗ <b>There's no such comic title!</b>")
        else:
            len_ = len(found_comics_list)
            if len_ == 1:
                await msg.reply(f"❗ <b>I found one:</b>")
                comic_id = found_comics_list[0]
                if is_cyrillic(user_input):
                    await state.update_data(lang='ru')
                    comic_data = await comics_db.get_ru_comic_data_by_id(comic_id)
                    await send_comic(msg.from_user.id, data=comic_data, comic_lang='ru')
                else:
                    comic_data = await comics_db.get_comic_data_by_id(comic_id)
                    await send_comic(msg.from_user.id, data=comic_data)

            elif len_ >= 2:
                await msg.reply(f"❗ <b>I found <u><b>{len_}</b></u> comics. </b>")
                await state.update_data(list=found_comics_list)
                if is_cyrillic(user_input):
                    await state.update_data(lang='ru')
                await trav_step(msg, state)  # dirty, but works!
