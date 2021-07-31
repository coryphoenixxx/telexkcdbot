import asyncio
import ujson

from random import randint
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.utils.exceptions import MessageNotModified

from loader import comics_db, users_db
from keyboard_ import kboard
from parser_ import parser
from config_ import *

from loader import bot, loop
from aiogram import Dispatcher

storage = RedisStorage('localhost', 6379, db=0)
dp = Dispatcher(bot, loop=loop, storage=storage)


# 472 Can't parse entities: unsupported start tag "span" at byte offset 40
# Error in _get_soup() for https://www.explainxkcd.com/532
# Error in get_explanation() for 532: 'NoneType' object has no attribute 'find_all'
# 532 name 'asyncio' is not defined
# 658 Wrong type of the web page content
# Error in _get_soup() for https://www.explainxkcd.com/1035
# Error in get_explanation() for 1035: 'NoneType' object has no attribute 'find_all'
# 1035 name 'asyncio' is not defined
# 1331 Message must be non-empty
# Error in _get_soup() for https://www.explainxkcd.com/1692
# Error in get_explanation() for 1692: 'NoneType' object has no attribute 'find_all'
# 1692 name 'asyncio' is not defined
# 1732 Wrong type of the web page content

async def check_last_comic():
    async def get_subscribed_users():
        for user_id in (await users_db.subscribed_users):
            yield user_id

    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = parser.latest_comic_id

    if real_last_comic_id > db_last_comic_id:
        for id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            data = await parser.get_full_comic_data(id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            async for user_id in get_subscribed_users():
                await bot.send_message(user_id, "<b>And here\'s new comic!</b> 🔥")
                comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
                await mod_answer(user_id, data=comic_data)
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            print(f"{count} messages successful sent.")  # TODO: add to log?


async def mod_answer(user_id: int, data: dict, keyboard=kboard.navigation):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data.values()

    await users_db.update_cur_comic_id(user_id, comic_id)  # TODO: replace by this all cur_comic_id?
    link = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'  # TODO: link or url?
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '')

    await bot.send_message(chat_id=user_id,
                           text=headline,
                           disable_web_page_preview=True)
    if is_specific:
        await bot.send_message(chat_id=user_id,
                               text=f"It's a peculiar comic! ^^ It's preferable to view it "
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
    await bot.send_message(chat_id=user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id),
                           disable_web_page_preview=True,
                           disable_notification=True)


@dp.message_handler(CommandStart())
async def start(message: Message):
    await users_db.new_user(message.from_user.id)
    bot_name = (await bot.me).username
    await message.answer(f"Hey! The <b>{bot_name}</b> at your disposal!\t\t\t<b>[¬º-°]¬</b>")
    await message.answer_photo(InputFile('static/bot_image.png'))
    await show_menu(message)


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
                              reply_markup=await kboard.menu(user_id))


@dp.message_handler(commands=['menu', 'help'])
async def show_menu(message: Message):
    help_text = """
Type in the <u><b>comic number</b></u> and I'll find it for you!
Type in the <u><b>comic title</b></u> and I'll try to find it for you!
***
You can subscribe for a new xkcd comic.
You can add comics to the bookmarks and read them later.
***
If something goes wrong or looks strange try to view a comic in your browser (I'll give you a link).
"""
    await message.answer(help_text, reply_markup=await kboard.menu(message.from_user.id))


@dp.callback_query_handler(Text('read_xkcd'))
async def read_xkcd(message: Message):
    cur_comic_id = await users_db.get_cur_comic(message.from_user.id)
    comic_data = await comics_db.get_comic_data_by_id(cur_comic_id)
    await mod_answer(message.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('user_bookmarks'))
async def show_bookmarks(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    bookmarks_list = await users_db.bookmarks(user_id)

    len_ = len(bookmarks_list)
    if not len_:
        await call.message.answer(f"You've no bookmarks.")
    else:
        await call.message.answer(f"You've <u><b>{len_}</b></u> bookmarks.")
        bookmarks_json = ujson.dumps(bookmarks_list)
        await state.update_data(json=bookmarks_json)
        await iter_step(call, state)


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
async def rus_version(call: CallbackQuery, keyboard=kboard.navigation):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    cur_comic_id = await users_db.get_cur_comic(call.from_user.id)
    comic_data = await comics_db.get_rus_version_data(cur_comic_id)
    await mod_answer(call.from_user.id, data=comic_data, keyboard=keyboard)


@dp.callback_query_handler(Text('iter_rus'))
async def iter_rus_version(call: CallbackQuery):
    await rus_version(call, keyboard=kboard.iteration)


@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery, keyboard=kboard.navigation):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    user_id = call.from_user.id
    cur_comic_id = await users_db.get_cur_comic(user_id)
    try:
        text, url = await parser.get_explanation(cur_comic_id)
        text = text.replace('<', '').replace('>', '')
        text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    except Exception as err:
        print(f"Can't get explanation!: {err}")  # TODO: log
        text = "Can't get explanation..."
    await call.message.answer(text=text,
                              reply_markup=await keyboard(user_id, cur_comic_id),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text('iter_explain'))  # TODO: remake
async def iter_explanation(call: CallbackQuery):
    await explanation(call, keyboard=kboard.iteration)


@dp.callback_query_handler(Text('bookmark'))
async def bookmark(call: CallbackQuery, keyboard=kboard.navigation):
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


@dp.callback_query_handler(Text('iter_bookmark'))
async def iter_bookmark(call: CallbackQuery):
    await bookmark(call, keyboard=kboard.iteration)


@dp.callback_query_handler(Text('iter_stop'))
async def iter_stop(call: CallbackQuery, state: FSMContext):
    await state.reset_data()
    user_id = call.from_user.id
    current_comic_id = await users_db.get_cur_comic(user_id)
    try:
        # await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
        await bot.send_message(text="It's all!",
                               chat_id=call.from_user.id,
                               reply_markup=await kboard.navigation(call.from_user.id, current_comic_id))

    except MessageNotModified:
        pass


@dp.callback_query_handler(Text('iter_step'))
async def iter_step(call: CallbackQuery, state: FSMContext):
    try:
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    except (AttributeError, MessageNotModified):
        pass
    try:
        json_obj = (await state.get_data())['json']
    except KeyError:
        pass
    else:
        list_ = ujson.loads(json_obj)
        try:
            comics_id = list_.pop(0)
            comic_data = await comics_db.get_comic_data_by_id(comics_id)
            json_obj = ujson.dumps(list_)
            await state.update_data(json=json_obj)
            await mod_answer(call.from_user.id, data=comic_data, keyboard=kboard.iteration)
        except IndexError:
            await iter_stop(call, state)




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


@dp.message_handler(commands='full_test')
@admin
async def full_test(message: Message):
    latest = parser.latest_comic_id
    for comic_id in range(1, latest + 1):
        try:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await mod_answer(ADMIN_ID, data=comic_data)
            await asyncio.sleep(1)

            if comic_id in parser.real_rus_ids:
                comic_data = await comics_db.get_rus_version_data(comic_id)
                await mod_answer(ADMIN_ID, data=comic_data)
                await asyncio.sleep(1)

            text, url = await parser.get_explanation(comic_id)
            text = text.replace('<', '').replace('>', '')
            text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
            await message.answer(text=text,
                                 reply_markup=await kboard.navigation(ADMIN_ID, comic_id),
                                 disable_web_page_preview=True)

            await asyncio.sleep(3)
        except Exception as err:
            print(comic_id, err)
            await asyncio.sleep(601)


"""ECHO"""


@dp.message_handler()
async def echo(message: Message, state: FSMContext):
    user_input = message.text.lower()
    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await message.answer(f"Please, enter a number between 1 and {latest}!")
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_cur_comic_id(message.from_user.id, comic_id)
            await mod_answer(message.from_user.id, data=comic_data)
    else:
        found_comics_list = await comics_db.get_comics_ids_by_title(user_input)
        if not found_comics_list:
            await message.answer(f"There's no such comic title!")
        else:
            len_ = len(found_comics_list)
            if len_ == 1:
                await message.answer(f"I found one:")
                await mod_answer(message.from_user.id, data=found_comics_list[0])
            elif len_ >= 2:
                await message.answer(f"I found <u><b>{len_}</b></u> xkcd comics containing "
                                     f"<b>\"{user_input}\"</b> in their titles."
                                     f"\nHere\'s last:")
                found_comics_json = ujson.dumps(found_comics_list)
                await state.update_data(json=found_comics_json)
                await iter_step(message, state)  # TODO: dirty
