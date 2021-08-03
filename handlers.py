import asyncio

from random import randint
from aiogram.types import Message, CallbackQuery, InputFile, Update
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked
from contextlib import suppress

from loader import comics_db, users_db, bot, loop
from keyboard_ import kboard
from parser_ import parser
from config_ import *

storage = RedisStorage2('localhost', 6379, db=0)
dp = Dispatcher(bot, loop=loop, storage=storage)


async def check_last_comic():
    async def get_subscribed_users():
        for user_id in (await users_db.subscribed_users):
            yield user_id

    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = parser.latest_comic_id

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            data = await parser.get_full_comic_data(comic_id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            async for user_id in get_subscribed_users():
                await bot.send_message(user_id, "<b>And here\'s new comic!</b> 🔥")
                comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
                await send_comic(user_id, data=comic_data)
                count += 1
                if count % 20 == 0:
                    await asyncio.sleep(0.5)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            print(f"{count} messages successful sent.")  # TODO: add to log?


async def send_comic(user_id: int, data: dict, keyboard=kboard.navigation):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data.values()

    await users_db.update_cur_comic_id(user_id, comic_id)
    link = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '')

    await bot.send_message(chat_id=user_id,
                           text=headline,
                           disable_web_page_preview=True)
    try:
        if is_specific:
            await bot.send_message(chat_id=user_id,
                                   text=f"❗❗❗ It's a peculiar comic! ^^ It's preferable to view it "
                                        f"in <a href='{link}'>your browser</a>.",
                                   disable_web_page_preview=True,
                                   disable_notification=True)
        if img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(chat_id=user_id,
                                 photo=img_url,
                                 disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(chat_id=user_id,
                                     animation=img_url,
                                     disable_notification=True)
        else:
            await bot.send_photo(chat_id=user_id,
                                 photo=InputFile('static/no_image.png'),
                                 disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest):
        await bot.send_message(chat_id=user_id,
                               text=f"❗❗❗ Can't get image, try your brower!",
                               disable_web_page_preview=True,
                               disable_notification=True)
    await bot.send_message(chat_id=user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id),
                           disable_web_page_preview=True,
                           disable_notification=True)


@dp.message_handler(CommandStart())
async def start(msg: Message):
    await users_db.add_user(msg.from_user.id)
    bot_name = (await bot.me).username
    await msg.answer(f"Hey! The <b>{bot_name}</b> at your disposal!\t\t\t<b>[¬º-°]¬</b>")
    await msg.answer_photo(InputFile('static/bot_image.png'))
    await show_menu(msg)


"""MENU"""


@dp.callback_query_handler(Text(endswith='subscribe'))
async def subscriber(call: CallbackQuery):
    user_id = call.from_user.id
    await users_db.subscribe(user_id) if call.data == 'subscribe' else await users_db.unsubscribe(user_id)

    with suppress(AttributeError, MessageNotModified):
        if 'subscribed' in call.message.text:
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id,
                                                reply_markup=None)

    inner_text = f"{call.data}d for" if call.data == 'subscribe' else f"{call.data}d from"
    await call.message.answer(f"❗ <b>You have been {inner_text} notification you whenever a new xkcd is released!</b>",
                              reply_markup=await kboard.menu(user_id))


@dp.message_handler(commands=['menu', 'help'])
async def show_menu(msg: Message):
    help_text = """
Type in the <u><b>comic number</b></u> and I'll find it for you!
Type in the <u><b>comic title</b></u> and I'll try to find it for you!

***
In menu you can:
— subscribe for a new xkcd comic.
— add comics to the bookmarks and read them later.
— remove RU button if it distracts you from reading.

***
❗❗❗
If something goes wrong or looks strange try to view a comic in your browser (I'll give you a link).
"""
    await msg.answer(help_text, reply_markup=await kboard.menu(msg.from_user.id))


@dp.callback_query_handler(Text(endswith='_ru'))
async def set_ru_button(call: CallbackQuery):
    action = call.data[:-3]
    lang = 'ru' if action == 'add' else 'en'
    await users_db.set_user_lang(call.from_user.id, lang)
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                            message_id=call.message.message_id,
                                            reply_markup=await kboard.menu(call.from_user.id))
    except (AttributeError, MessageNotModified):
        pass


@dp.callback_query_handler(Text('read_xkcd'))
async def read_xkcd(msg: Message):
    comic_data = await comics_db.get_comic_data_by_id(1)
    await send_comic(msg.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('read_xkcd'))
async def read_xkcd(msg: Message):
    comic_data = await comics_db.get_comic_data_by_id(1)
    await send_comic(msg.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('user_bookmarks'))
async def show_bookmarks(call: CallbackQuery, state: FSMContext):
    bookmarks_list = await users_db.get_bookmarks(call.from_user.id)
    len_ = len(bookmarks_list)
    if not len_:
        await call.message.answer(f"❗ You've no bookmarks.")
    else:
        await call.message.answer(f"❗ You've <u><b>{len_}</b></u> bookmarks.")
        await state.update_data(list=bookmarks_list)
        await trav_step(call, state)


"""MAIN"""


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    with suppress(AttributeError, MessageNotModified):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    cur_comic_id = await users_db.get_cur_comic_id(call.from_user.id)
    action = call.data.split('_')[1]
    latest = parser.latest_comic_id

    actions = {
        'first': 1,
        'prev': cur_comic_id - 1,
        'random': randint(1, latest),
        'next': cur_comic_id + 1,
        'last': latest
    }
    new_comic_id = actions.get(action)

    if new_comic_id <= 0:
        new_comic_id = latest
    if new_comic_id > latest:
        new_comic_id = 1

    await users_db.update_cur_comic_id(call.from_user.id, new_comic_id)
    comic_data = await comics_db.get_comic_data_by_id(new_comic_id)
    await send_comic(call.from_user.id, data=comic_data)


@dp.callback_query_handler(Text(endswith='ru'))
async def ru_version(call: CallbackQuery, keyboard=kboard.navigation):
    if 'trav' in call.data:
        keyboard = kboard.traversal

    with suppress(AttributeError, MessageNotModified):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    cur_comic_id = await users_db.get_cur_comic_id(call.from_user.id)
    comic_data = await comics_db.get_ru_version_data(cur_comic_id)
    await send_comic(call.from_user.id, data=comic_data, keyboard=keyboard)


@dp.callback_query_handler(Text(endswith='explain'))
async def explanation(call: CallbackQuery, keyboard=kboard.navigation):
    if 'trav' in call.data:
        keyboard = kboard.traversal

    with suppress(AttributeError, MessageNotModified):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    user_id = call.from_user.id
    cur_comic_id = await users_db.get_cur_comic_id(user_id)
    try:
        text, url = await parser.get_explanation(cur_comic_id)
        text = text.replace('<', '').replace('>', '')
        text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    except Exception as err:
        print(f"Can't get explanation!: {err}")  # TODO: log
        text = "❗ Can't get explanation..."
    await call.message.answer(text=text,
                              reply_markup=await keyboard(user_id, cur_comic_id),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text(endswith='bookmark'))
async def bookmark(call: CallbackQuery, keyboard=kboard.navigation):
    if 'trav' in call.data:
        keyboard = kboard.traversal

    user_id = call.from_user.id
    cur_comic_id = await users_db.get_cur_comic_id(user_id)
    user_bookmarks_list = await users_db.get_bookmarks(user_id)

    if cur_comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(cur_comic_id)
        text = f"❗ <b>Comic {cur_comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(cur_comic_id)
        text = f"❗ <b>Comic {cur_comic_id} has been <u>added</u> to your bookmarks!</b>"

    await users_db.update_bookmarks(user_id, user_bookmarks_list)

    with suppress(AttributeError, MessageNotModified):
        if 'your bookmarks' in call.message.text:
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id,
                                                reply_markup=None)

    await call.message.answer(text, reply_markup=await keyboard(user_id, cur_comic_id))


"""TRAVERSAL"""


@dp.callback_query_handler(Text('trav_stop'))
async def trav_stop(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    current_comic_id = await users_db.get_cur_comic_id(user_id)

    with suppress(MessageNotModified):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                            message_id=call.message.message_id,
                                            reply_markup=await kboard.navigation(call.from_user.id,
                                                                                 current_comic_id))
    await state.reset_data()


@dp.callback_query_handler(Text('trav_step'))
async def trav_step(call: (CallbackQuery, Message), state: FSMContext):
    with suppress(AttributeError, MessageNotModified):
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    list_ = (await state.get_data())['list']
    try:
        comic_data = await comics_db.get_comic_data_by_id(list_.pop(0))
    except IndexError:
        await trav_stop(call, state)
    else:
        await send_comic(call.from_user.id, data=comic_data, keyboard=kboard.traversal)
        await state.update_data(list=list_)


"""ADMIN'S"""


# TODO: create admin panel
# TODO: add opportunity to add comic to specifics
# TODO: get users number


def admin(func):
    async def wrapper(msg: Message):
        if msg.from_user.id != int(ADMIN_ID):
            await msg.answer('Nope!')
        else:
            await func(msg)

    return wrapper


@dp.message_handler(commands='full_test')
@admin
async def full_test(msg: Message):
    latest = parser.latest_comic_id
    for comic_id in range(1, latest + 1):
        try:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await send_comic(ADMIN_ID, data=comic_data)
            await asyncio.sleep(1)

            if comic_id in parser.real_ru_ids:
                comic_data = await comics_db.get_ru_version_data(comic_id)
                await send_comic(ADMIN_ID, data=comic_data)
                await asyncio.sleep(1)

            text, url = await parser.get_explanation(comic_id)
            text = text.replace('<', '').replace('>', '')
            text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
            await msg.answer(text=text,
                             reply_markup=await kboard.navigation(ADMIN_ID, comic_id),
                             disable_web_page_preview=True)

            await asyncio.sleep(3)
        except Exception as err:
            print(comic_id, err)
            await asyncio.sleep(601)


"""DEFAULT INPUT"""


@dp.message_handler()
async def default(msg: Message, state: FSMContext):
    user_input = msg.text.lower()
    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await msg.answer(f"❗❗❗ Please, enter a number between 1 and {latest}!")
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_cur_comic_id(msg.from_user.id, comic_id)
            await send_comic(msg.from_user.id, data=comic_data)
    else:
        found_comics_list = await comics_db.get_comics_ids_by_title(user_input)
        if not found_comics_list:
            await msg.answer(f"❗ There's no such comic title!")
        else:
            len_ = len(found_comics_list)
            if len_ == 1:
                await msg.answer(f"❗ I found one:")
                await send_comic(msg.from_user.id, data=found_comics_list[0])
            elif len_ >= 2:
                await msg.answer(f"❗ I found <u><b>{len_}</b></u> xkcd comics containing "
                                 f"<b>\"{user_input}\"</b> in their titles.")
                await state.update_data(list=found_comics_list)
                await trav_step(msg, state)


# TODO: implement
@dp.errors_handler(exception=BotBlocked)
async def bot_blocked_error(update: Update, exception: BotBlocked):
    # logger.exception(f'Bot blocked by user {update.msg.from_user.id}')
    # return True
    pass


