import asyncio
import random

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, executor

from parser_ import get_comic
from config import Config


loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN)
dp = Dispatcher(bot, loop=loop)

LAST = 2485
CUR_NUM = 0


def get_keyboard():
    buttons = [
        InlineKeyboardButton(text='<<First', callback_data='first'),
        InlineKeyboardButton(text='<Prev', callback_data='prev'),
        InlineKeyboardButton(text='Random', callback_data='random'),
        InlineKeyboardButton(text='Next>', callback_data='next'),
        InlineKeyboardButton(text='Last>>', callback_data='last')
    ]

    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(*buttons)
    return keyboard


async def notify_admin(dp):
    await bot.send_message(chat_id=Config.ADMIN_ID, text="Bot in Your Power, My Lord!")


@dp.message_handler(commands=['start', 'help'])
async def hello(message: Message):
    await message.answer('Hi! I\'m TeleXKCDbot')
    await asyncio.sleep(1)
    await message.answer('Write the xkcd-comic\'s number')


@dp.message_handler(commands="read")
async def cmd_random(message: Message):
    user_input = 1000
    img_url = get_comic(user_input)
    await message.answer_photo(photo=img_url)
    await message.answer("Нажми!", reply_markup=get_keyboard())


@dp.callback_query_handler(text='first')
async def first_f(call: CallbackQuery):
    global CUR_NUM
    CUR_NUM = 1

    img_url = get_comic(1)
    await call.message.answer_photo(photo=img_url)
    await call.message.answer("1", reply_markup=get_keyboard())


@dp.callback_query_handler(text='prev')
async def prev_f(call: CallbackQuery):
    global CUR_NUM
    num = CUR_NUM - 1
    if num == 0:
        num = LAST
    CUR_NUM = num

    img_url = get_comic(num)
    await call.message.answer_photo(photo=img_url)
    await call.message.answer(str(num), reply_markup=get_keyboard())


@dp.callback_query_handler(text='random')
async def random_f(call: CallbackQuery):
    global CUR_NUM
    num = random.randint(1, LAST)
    CUR_NUM = num

    try:
        img_url = get_comic(num)
        await call.message.answer_photo(photo=img_url)
        await call.message.answer(str(num), reply_markup=get_keyboard())
    except:
        print(num)


@dp.callback_query_handler(text='next')
async def next_f(call: CallbackQuery):
    global CUR_NUM
    num = CUR_NUM + 1
    if num > LAST:
        num = 1
    CUR_NUM = num

    img_url = get_comic(num)
    await call.message.answer_photo(photo=img_url)
    await call.message.answer(str(num), reply_markup=get_keyboard())


@dp.callback_query_handler(text='last')
async def last_f(call: CallbackQuery):
    global CUR_NUM
    CUR_NUM = LAST
    img_url = get_comic(LAST)
    await call.message.answer_photo(photo=img_url)
    await call.message.answer(str(LAST), reply_markup=get_keyboard())


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text
    if user_input.isdigit():
        img_url = get_comic(user_input)
        await message.answer_photo(photo=img_url)
    else:
        await message.answer('Please, write a number!')


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=notify_admin)
