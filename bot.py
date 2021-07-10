import asyncio
import random

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor

from parser_ import get_comic, BASE_URL, get_rus_version, get_eng_explanation
from config import Config

loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop)


LAST = 2486
CUR_NUM = 0


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
    await bot.send_message(chat_id=Config.ADMIN_ID, text="...Bot in Your Power, My Lord...")


@dp.message_handler(commands=['start', 'help'])
async def hello(message: Message):
    await message.answer("Hey! I'm xkcd bot.\n")
    await asyncio.sleep(1.5)
    await message.answer("Here is my list of commands:\n"
                         "- Type in the comic number and I'll find it for you!\n"
                         "Type nothing and I'll send you the latest xkcd.\n"
                         "/read - read-mode\n"
                         "/subscribe - I'll notify you whenever a new xkcd is released.\n"
                         "/unsubscribe - I'll stop notifying you when new xkcd comics are released.\n"
                         "/fav - I'll send you your bookmarks.\n"
                         "/random - I'll send you a random xkcd.")


async def ext_answer(message: Message, data: dict):
    num, title, img_url, comment = data.values()

    await message.answer(text=f"<b>{str(num)}. \"<a href='{BASE_URL + str(num)}'>{title}</a>\"</b>",
                         disable_web_page_preview=True, disable_notification=True)

    if img_url.endswith(('.png', '.jpg')):
        await message.answer_photo(photo=img_url)
    elif img_url.endswith('.gif'):
        await message.answer_animation(animation=img_url)
    else:
        await message.answer("Can\'t upload pic/gif...\nUse browser to read comic.")

    await message.answer(f'<i>{comment}</i>', reply_markup=get_keyboard(), disable_notification=True)


@dp.message_handler(commands="read")
async def cmd_read(message: Message):
    global CUR_NUM
    default_num = 404  # 1608, 1190, 1416, 404, 1037, 1538, 1953, 1965(div) - defective
    CUR_NUM = default_num
    img_data = get_comic(default_num)
    await ext_answer(message, img_data)


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    global CUR_NUM
    action = call.data.split('_')[1]

    actions = {
        'first': 1,
        'prev': CUR_NUM - 1,
        'random': random.randint(1, LAST),
        'next': CUR_NUM + 1,
        'last': LAST
    }

    num = actions.get(action)

    if num <= 0:
        num = LAST
    if num > LAST:
        num = 1

    CUR_NUM = num

    img_data = get_comic(num)
    await ext_answer(call.message, img_data)


@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery):
    global CUR_NUM
    data = get_rus_version(CUR_NUM)
    if data:
        await ext_answer(call.message, data)
    else:
        await call.message.answer('There\'s no russian version...(((')


@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery):
    global CUR_NUM
    text = get_eng_explanation(CUR_NUM)
    await call.message.answer(text)


@dp.message_handler()
async def echo(message: Message):
    global CUR_NUM
    user_input = message.text
    if user_input.isdigit():
        num = int(user_input)
        comic_data = get_comic(num)
        CUR_NUM = num
        await ext_answer(message, data=comic_data)
    else:
        await message.answer('Please, write a number or command!')


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=notify_admin)
