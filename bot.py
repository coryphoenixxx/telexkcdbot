import asyncio
import random


from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor

from parser_ import Parser
from config_ import Config
from database_ import *

loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop)


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
    add_new_user(message.from_user.id)
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
    # headline = f"<b>{num}. \"<a href='{'https://xkcd.com/' + num}'>{title}</a>\"</b>   <i>({day}-{month}-{year})</i>"
    # text = f"{first_p}<i><b><a href='{url}'>...continue</a></b></i>"


    headline, img_url, comment = data.values()

    await message.answer(text=headline, disable_web_page_preview=True, disable_notification=True)
    if img_url.endswith(('.png', '.jpg')):
        await message.answer_photo(photo=img_url)
    elif img_url.endswith('.gif'):
        await message.answer_animation(animation=img_url)
    else:
        await message.answer("Can\'t upload pic/gif...\nUse browser to read comic.")
    await message.answer(f'<i>{comment}</i>', reply_markup=get_keyboard(), disable_web_page_preview=True,
                         disable_notification=True)


@dp.message_handler(commands="read")
async def cmd_read(message: Message):
    default_num = 1488
    update_user_current_comic(message.from_user.id, default_num)
    img_data = get_comic(default_num)
    await ext_answer(message, img_data)


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    # TAKE OUT NAV LOGIC
    current_comic = get_user_current_comic(call.from_user.id)
    action = call.data.split('_')[1]

    actions = {
        'first': 1,
        'prev': current_comic - 1,
        'random': random.randint(1, LAST),
        'next': current_comic + 1,
        'last': LAST
    }

    num = actions.get(action)

    if num <= 0:
        num = LAST
    if num > LAST:
        num = 1

    update_user_current_comic(call.from_user.id, num)

    data = get_comic(num)
    await ext_answer(call.message, data)


# GET RUSSIAN VERSION
@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery):
    current_comic = get_user_current_comic(call.from_user.id)
    data = get_rus_version(current_comic)
    if data:
        await ext_answer(call.message, data)
    else:
        await call.message.answer('Unfortunately there\'s no russian version... ;(((')


# GET EXPLANATION
@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery):
    current_comic = get_user_current_comic(call.from_user.id)
    text = get_explanation(current_comic)
    await call.message.answer(text, disable_web_page_preview=True)


# RANDOM USER INPUT
@dp.message_handler()
async def echo(message: Message):
    user_input = message.text
    if user_input.isdigit():
        num = int(user_input)
        comic_data = get_comic(num)
        update_user_current_comic(message.from_user.id, num)
        await ext_answer(message, data=comic_data)
    else:
        await message.answer('Please, write a number or command!')


if __name__ == "__main__":
    # HERE MUST BE MICROSERVICE
    create_users_database()
    executor.start_polling(dp, on_startup=notify_admin)
