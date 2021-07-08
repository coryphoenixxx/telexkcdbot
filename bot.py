import asyncio
import random

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor

from parser_ import get_comic, BASE_URL
from config import Config

loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop)

LAST = 2485
CUR_NUM = 0


def get_keyboard():
    buttons = [
        InlineKeyboardButton(text='<<First', callback_data='nav_first'),
        InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        InlineKeyboardButton(text='Random', callback_data='nav_random'),
        InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        InlineKeyboardButton(text='Last>>', callback_data='nav_last'),
        # InlineKeyboardButton(text='Favorite', callback_data=''),
        # InlineKeyboardButton(text='Subscribe>>', callback_data='')
    ]

    keyboard = InlineKeyboardMarkup(row_width=5,)
    keyboard.add(*buttons)
    return keyboard


async def notify_admin(dp):
    await bot.send_message(chat_id=Config.ADMIN_ID, text="...Bot in Your Power, My Lord...")


@dp.message_handler(commands=['start', 'help'])
async def hello(message: Message):
    await message.answer('Hi! I\'m TeleXKCDbot')
    await asyncio.sleep(1)
    await message.answer('Write the xkcd-comic\'s number')


async def ext_answer(message: Message, data: dict):
    num, title, img_url, comment = data.values()

    await message.answer(text=f"<b>{str(num)}. \"<a href='{BASE_URL + str(num)}'>{title}</a>\"</b>",
                         disable_web_page_preview=True)

    if img_url.endswith(('.png', '.jpg')):
        await message.answer_photo(photo=img_url)
    elif img_url.endswith('.gif'):
        await message.answer_animation(animation=img_url)
    else:
        await message.answer("Can\'t upload pic/gif...\nUse browser to read comic.")

    await message.answer(f'<i>{comment}</i>', reply_markup=get_keyboard())


@dp.message_handler(commands="read")
async def cmd_read(message: Message):
    default_num = 1608  #1608, 1190, 1416 - defective
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


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text
    if user_input.isdigit():
        img_url = get_comic(user_input).get('img_url')
        await message.answer_photo(photo=img_url)
    else:
        await message.answer('Please, write a number!')


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=notify_admin)
