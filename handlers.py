import asyncio

from random import randint
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils.exceptions import MessageNotModified

from app import mod_answer
from loader import comics_db, users_db
from keyboard_ import kb
from parser_ import parser
from config_ import *


from loader import bot, loop
from aiogram import Dispatcher

dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())
# dp = Dispatcher(bot, loop=loop, storage=RedisStorage2('localhost', 6379, db=5, pool_size=10))


@dp.message_handler(CommandStart())
async def start(message: Message):
    await users_db.new_user(message.from_user.id)
    bot_name = (await bot.me).username
    await message.answer(f"Hey! The <b>{bot_name}</b> at your disposal!\t\t\t<b>[¬º-°]¬</b>")
    await message.answer_photo(InputFile('static/bot_image.png'))
    await menu(message)


@dp.callback_query_handler(Text(endswith='subscribe'))
async def subscriber(call: CallbackQuery):
    user_id = call.from_user.id
    await users_db.subscribe(user_id) if call.data == 'subscribe' else await users_db.unsubscribe(user_id)

    try:
        if 'subscribed' in call.message.text:
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id,
                                                reply_markup=None)
    except (AttributeError, MessageNotModified):
        pass
    inner_text = f"{call.data}d for" if call.data == 'subscribe' else f"{call.data}d from"
    await call.message.answer(f"<b>You have been {inner_text} notification you whenever a new xkcd is released!</b>",
                              reply_markup=await kb.menu(user_id))


@dp.message_handler(commands=['menu', 'help'])
async def menu(message: Message):
    help_text = """
Type in the <u><b>comic number</b></u> and I'll find it for you!
Type in the <u><b>comic title</b></u> and I'll try to find it for you!

You can subscribe for a new xkcd comic.
You can add comics to the bookmarks and read them later.
***
If something goes wrong or looks strange try to view a comic in browser (I'll give you a link).
"""
    # try:
    #     await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=message.message_id)
    # except MessageNotModified:
    #     pass
    await message.answer(help_text, reply_markup=await kb.menu(message.from_user.id))


@dp.callback_query_handler(Text('read_xkcd'))
async def read_xkcd(message: Message):
    # TODO: for some reason don't remove previous keyboard
    try:
        await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    comic_data = await comics_db.get_comic_data_by_id(1)
    await users_db.update_cur_comic_id(message.from_user.id, 1)
    await mod_answer(message.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('bookmarks'))
async def show_bookmarks(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    bookmarks = await users_db.bookmarks(user_id)
    bookmarks_iter = iter(bookmarks)
    await state.update_data(iter=bookmarks_iter)
    len_ = len(bookmarks)
    if len_:
        await call.message.answer(f"You have <u><b>{len(bookmarks)}</b></u> bookmarks.")
        await go_next(call, state)
    else:
        await call.message.answer(f"You have not bookmarks.")


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass

    cur_comic_id = await users_db.get_cur_comic(call.from_user.id)
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
    await mod_answer(call.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery, keyboard=kb.navigation):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    cur_comic_id = await users_db.get_cur_comic(call.from_user.id)
    comic_data = await comics_db.get_rus_version_data(cur_comic_id)
    await mod_answer(call.from_user.id, data=comic_data, keyboard=keyboard)


@dp.callback_query_handler(Text('rl_rus'))
async def rl_rus_version(call: CallbackQuery):
    await rus_version(call, keyboard=kb.stop_next)


@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery, keyboard=kb.navigation):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    user_id = call.from_user.id
    cur_comic_id = await users_db.get_cur_comic(user_id)
    text, url = await parser.get_explanation(cur_comic_id)
    text = text.replace('<', '').replace('>', '')
    text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    await call.message.answer(text=text,
                              reply_markup=await keyboard(user_id, cur_comic_id),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text('rl_explain'))
async def rl_explanation(call: CallbackQuery):
    await explanation(call, keyboard=kb.stop_next)


@dp.callback_query_handler(Text('bookmark'))
async def bookmark(call: CallbackQuery, keyboard=kb.navigation):
    user_id = call.from_user.id
    cur_comic_id = await users_db.get_cur_comic(user_id)
    user_bookmarks_list = await users_db.bookmarks(user_id)
    if cur_comic_id in user_bookmarks_list:
        user_bookmarks_list.remove(cur_comic_id)
        text = f"<b>Comic {cur_comic_id} has been <u>removed</u> from your bookmarks!</b>"
    else:
        user_bookmarks_list.append(cur_comic_id)
        text = f"<b>Comic {cur_comic_id} has been <u>added</u> to your bookmarks!</b>"
    await users_db.update_bookmarks(user_id, user_bookmarks_list)
    try:
        if 'your bookmarks' in call.message.text:
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id,
                                                reply_markup=None)
    except (AttributeError, MessageNotModified):
        pass
    await call.message.answer(text, reply_markup=await keyboard(user_id, cur_comic_id))


@dp.callback_query_handler(Text('rl_bookmark'))
async def rl_bookmark(call: CallbackQuery):
    await bookmark(call, keyboard=kb.stop_next)


@dp.callback_query_handler(Text('stop'))
async def stop_func(call: CallbackQuery, state: FSMContext):
    await state.reset_data()
    user_id = call.from_user.id
    current_comic_id = await users_db.get_cur_comic(user_id)
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                        message_id=call.message.message_id,
                                        reply_markup=await kb.navigation(call.from_user.id, current_comic_id))
    except MessageNotModified:
        pass


@dp.callback_query_handler(Text('go_next'))
async def go_next(call: CallbackQuery, state: FSMContext):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    try:
        iter_ = (await state.get_data())['iter']
        i = next(iter_)
        comic_data = await comics_db.get_comic_data_by_id(i)
    except KeyError:
        pass
    except StopIteration:
        await stop_func(call, state)
    else:
        await state.update_data(iter=iter_)
        await mod_answer(call.from_user.id, data=comic_data, keyboard=kb.stop_next)


"""ADMIN'S"""
# TODO: create admin panel
# TODO: add opportunity to add comic to specifics
# TODO: get users number


def admin(func):
    async def wrapper(message: Message):
        if message.from_user.id != int(ADMIN_ID):
            await message.answer('Nope!')
        else:
            await func(message)

    return wrapper


@dp.message_handler(commands='test')
@admin
async def full_test(message: Message):
    latest = parser.get_latest_comic_id()
    for comic_id in range(1, ):
        try:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await mod_answer(ADMIN_ID, data=comic_data)
            await asyncio.sleep(1)

            text, url = await parser.get_explanation(comic_id)
            text = text.replace('<', '').replace('>', '')
            text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
            await message.answer(text=text,
                                 reply_markup=await kb.navigation(ADMIN_ID, comic_id),
                                 disable_web_page_preview=True)

            await asyncio.sleep(3)
        except Exception as err:
            print(comic_id, err)
            await asyncio.sleep(600)


"""ECHO"""


@dp.message_handler()
async def echo(message: Message, state: FSMContext):
    user_input = message.text.lower()
    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await message.answer(f"Please, enter a number between 1 and {latest})!")
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_cur_comic_id(message.from_user.id, comic_id)
            await mod_answer(message.from_user.id, data=comic_data)
    else:
        comic_list = await comics_db.get_comics_ids_by_title(user_input)
        if not comic_list:
            await message.answer(f"There's no such comic title!")
        else:
            len_ = len(comic_list)
            if len_ >= 2:
                comic_iter = iter(comic_list)
                await message.answer(f"I found <u><b>{len_}</b></u> xkcd comics containing "
                                     f"<b>\"{user_input}\"</b> in their titles."
                                     f"\nHere\'s last:")
                await state.update_data(iter=comic_iter)
                await go_next(message, state)  # TODO: dirty
            elif len_ == 1:
                await message.answer(f"I found one:")
                await mod_answer(message.from_user.id, data=comic_list[0])
