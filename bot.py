import asyncio
import random

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor

from parser_ import Parser
from config_ import Config
from database_ import ComicsDatabase, UsersDatabase


loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop)

parser = Parser()
users_db = UsersDatabase()
comics_db = ComicsDatabase()


def get_keyboard():
    buttons = [
        InlineKeyboardButton(text='|<', callback_data='nav_first'),
        InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        InlineKeyboardButton(text='>|', callback_data='nav_last'),
        InlineKeyboardButton(text='Bookmark\u2606', callback_data='fav'),
        InlineKeyboardButton(text='Explain', callback_data='explain'),
        InlineKeyboardButton(text='Rus', callback_data='rus'),
    ]

    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(*buttons)
    return keyboard


async def notify_admin(dp: Dispatcher):
    await dp.skip_updates()
    await bot.send_message(chat_id=Config.ADMIN_ID, text="...Bot in Your Power, My Lord...\t[¬º-°]¬")


@dp.message_handler(commands=['start', 'help'])
async def hello(message: Message):
    users_db.add_new_user(message.from_user.id)
    await message.answer("Hey! I'm xkcd bot. [¬º-°]¬\n")
    await asyncio.sleep(1.5)
    await message.answer("Here is my list of commands:\n"
                         "- Type in the comic number and I'll find it for you!\n"
                         "Type nothing and I'll send you the latest xkcd.\n"
                         "/read - read-mode\n"
                         "/subscribe - I'll notify you whenever a new xkcd is released.\n"
                         "/unsubscribe - I'll stop notifying you when new xkcd comics are released.\n"
                         "/fav - I'll send you your bookmarks.\n"
                         "/random - I'll send you a random xkcd.")


async def ext_answer(message: Message, comic_id: int, data: dict):
    if comic_id == 404:
        pass
    title, img_url, comment, public_date = data.values()
    headline = f"""<b>{comic_id}. \"<a href='{'https://xkcd.com/' + str(comic_id)}'>{title}</a>\"</b>\
                \n<i>({public_date})</i>"""

    await message.answer(text=headline,
                         disable_web_page_preview=True,
                         disable_notification=True)
    if img_url.endswith(('.png', '.jpg')):
        await message.answer_photo(photo=img_url)
    elif img_url.endswith('.gif'):
        await message.answer_animation(animation=img_url)
    else:
        await message.answer("Can\'t upload pic/gif...\nUse browser to see comic.")
    await message.answer(f'<i>{comment}</i>',
                         reply_markup=get_keyboard(),
                         disable_web_page_preview=True,
                         disable_notification=True)


@dp.message_handler(commands="read")
async def cmd_read(message: Message):
    default_num = 1488
    users_db.update_user_current_comic(message.from_user.id, default_num)
    data = comics_db.get_original_comic_data(default_num)
    await ext_answer(message, comic_id=default_num, data=data)


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    # TAKE OUT NAV LOGIC
    current_comic_id = users_db.get_user_current_comic(call.from_user.id)
    action = call.data.split('_')[1]
    LAST = 2489
    actions = {
        'first': 1,
        'prev': current_comic_id - 1,
        'random': random.randint(1, LAST),
        'next': current_comic_id + 1,
        'last': LAST
    }

    new_comic_id = actions.get(action)

    if new_comic_id <= 0:
        new_comic_id = LAST
    if new_comic_id > LAST:
        new_comic_id = 1

    users_db.update_user_current_comic(call.from_user.id, new_comic_id)

    data = comics_db.get_original_comic_data(new_comic_id)
    await ext_answer(call.message, comic_id=new_comic_id, data=data)


# GET RUSSIAN VERSION
@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery):
    current_comic_id = users_db.get_user_current_comic(call.from_user.id)
    data = comics_db.get_rus_version_data(current_comic_id)
    if not list(data.values())[0]:
        await call.message.answer('Unfortunately there\'s no russian version... ;(((')
    else:
        await ext_answer(call.message, comic_id=current_comic_id, data=data)


# GET EXPLANATION
@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery):
    current_comic_id = users_db.get_user_current_comic(call.from_user.id)
    text, url = comics_db.get_explanation_data(current_comic_id)
    text = f"{text}<i><b><a href='{url}'>...continue</a></b></i>"
    await call.message.answer(text, disable_web_page_preview=True)


# RANDOM USER INPUT
@dp.message_handler()
async def echo(message: Message):
    user_input = message.text
    if user_input.isdigit():
        num = int(user_input)
        comic_data = comics_db.get_original_comic_data(num)
        users_db.update_user_current_comic(message.from_user.id, num)
        await ext_answer(message, comic_id=num, data=comic_data)
    elif not user_input:
        pass    # IMPLEMENT
    else:
        # IMPLEMENT SEARCH BY WORD
        await message.answer('Please, write a number or command!')


def get_users():
    yield from (1219788543,)


async def check_last_comic():
    current_db_last_comic_number = comics_db.get_last_comic_id()
    real_current_last_comic_number = parser.get_last_comic_number()

    if real_current_last_comic_number > current_db_last_comic_number:
        data = parser.get_full_comic_data(real_current_last_comic_number)
        comic_values = tuple(data.values())
        # comics_db.add_new_comic(comic_values)
        print(comic_values)

    count = 0
    try:
        for user_id in get_users():
            if await bot.send_message(user_id, '<b>There new comic!</b>'):
                count += 1
        await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        print(f"{count} messages successful sent.")



def repeat(coro, loop):
    DELAY = 5
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == "__main__":
    users_db.create_users_database()

    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, check_last_comic, loop)
    executor.start_polling(dp, on_startup=notify_admin)
    print('Hahaha')
