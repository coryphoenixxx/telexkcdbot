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

help_text = """
<b><u>Here is my list of commands</u></b>:
 Type in the <b>comic number</b> and I'll find it for you!
 Type in the <b>comic title</b> and I'll try to find it for you!
 <b>/read</b> - Read-mode.
 <b>/subscribe</b> - I'll notify you whenever a new xkcd is released.
 <b>/unsubscribe</b> - I'll stop notifying you when new xkcd comics are released.
 <b>/bookmarks</b> - I'll send you your bookmarks.
 <b>/help</b> - I'll send you this text.
 """


def get_keyboard():
    buttons = [
        InlineKeyboardButton(text='|<<', callback_data='nav_first'),
        InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        InlineKeyboardButton(text='>>|', callback_data='nav_last'),
        InlineKeyboardButton(text='Bookmark\u2606', callback_data='fav'),
        InlineKeyboardButton(text='Explain', callback_data='explain'),
        InlineKeyboardButton(text='Rus', callback_data='rus'),
    ]

    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(*buttons)
    return keyboard


async def notify_admin(dp: Dispatcher):
    await dp.skip_updates()
    await users_db.create_users_database()
    await users_db.add_new_user(Config.ADMIN_ID)
    await bot.send_message(chat_id=Config.ADMIN_ID, text="<b>Bot in Your Power, My Lord...</b>")


@dp.message_handler(commands='start')
async def start(message: Message):
    await users_db.add_new_user(message.from_user.id)
    await message.answer("Hey! I'm xkcd-bot. [¬º-°]¬\n")
    await asyncio.sleep(1)
    await message.answer(help_text)


@dp.message_handler(commands='help')
async def help(message: Message):
    await message.answer(help_text)


async def mod_answer(message: Message, data: dict):
    comic_id, title, img_url, comment, public_date = data.values()
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
    await users_db.update_user_current_comic(message.from_user.id, 1)
    data = await comics_db.get_comic_data_by_id(1)
    await mod_answer(message,  data=data)


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    action = call.data.split('_')[1]
    latest = parser.latest_comic_id

    actions = {
        'first': 1,
        'prev': current_comic_id - 1,
        'random': random.randint(1, latest),
        'next': current_comic_id + 1,
        'last': latest
    }
    new_comic_id = actions.get(action)

    if new_comic_id <= 0:
        new_comic_id = latest
    if new_comic_id > latest:
        new_comic_id = 1

    await users_db.update_user_current_comic(call.from_user.id, new_comic_id)

    data = await comics_db.get_comic_data_by_id(new_comic_id)
    await mod_answer(call.message, data=data)


@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery):
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    data = await comics_db.get_rus_version_data(current_comic_id)
    if not list(data.values())[1]:
        await call.message.answer('Нет перевода ;(((')
    else:
        await mod_answer(call.message, data=data)


@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery):
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    text, url = parser.get_explanation(current_comic_id)
    text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    await call.message.answer(text, disable_web_page_preview=True)


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text

    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await message.answer(f'Please, write a number (1 - {latest})')
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_user_current_comic(message.from_user.id, comic_id)
            await mod_answer(message, data=comic_data)
    else:
        title = user_input
        comic_data = await comics_db.get_comic_data_by_title(title)
        if not comic_data:
            await message.answer(f"There's no this title!")
        else:
            await users_db.update_user_current_comic(message.from_user.id, comic_data.get('comic_id'))
            await mod_answer(message, data=comic_data)





def get_users():
    for user_id in (1219788543,):
        yield user_id


async def check_last_comic():
    current_db_last_comic_number = await comics_db.get_last_comic_id()
    real_current_last_comic_number = parser.get_and_update_latest_comic_id()

    if real_current_last_comic_number > current_db_last_comic_number:
        data = parser.get_full_comic_data(real_current_last_comic_number)
        comic = tuple(data.values())
        # await comics_db.add_new_comic(comic)

    count = 0
    try:
        for user_id in get_users():
            if await bot.send_message(user_id, '<b>There new comic!</b>'):
                count += 1
        await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        print(f"{count} messages successful sent.")


def repeat(coro, loop):
    delay = 60 * 10
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.call_later(5, repeat, check_last_comic, loop)
    executor.start_polling(dp, on_startup=notify_admin)
