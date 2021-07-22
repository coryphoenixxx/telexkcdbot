import asyncio
import random

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputFile
from aiogram.dispatcher.filters import Text
from aiogram.utils.executor import start_webhook, start_polling

from parser_ import Parser
from config_ import Config
from database_ import ComicsDatabase, UsersDatabase


loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop)


WEBHOOK_HOST = f'https://{Config.HEROKU_APP_NAME}.herokuapp.com'

WEBHOOK_PATH = f'/webhook/{Config.API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
PORT = Config.PORT


parser = Parser()
users_db = UsersDatabase()
comics_db = ComicsDatabase()


help_text = """
<b><u>Here is my list of commands</u></b>:
 Type in the <b>comic number</b> and I'll find it for you!
 Type in the <b>comic title</b> and I'll try to find it for you!
 <b>/subscribe</b> - I'll notify you whenever a new xkcd comics is released.
 <b>/unsubscribe</b> - I'll stop notifying you when new xkcd comics are released.
 <b>/bookmarks</b> - I'll send you your bookmarks.
 <b>/help</b> - I'll send you this text.
 """

specific_comic_ids = (1350, 1608, 1190, 1416, 1037,
                      980, 1110, 1525, 2198, 1975)


def get_keyboard():
    buttons = [
        InlineKeyboardButton(text='|<<', callback_data='nav_first'),
        InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        InlineKeyboardButton(text='>>|', callback_data='nav_last'),
        InlineKeyboardButton(text='Bookmark\u2606', callback_data='bookmark'),
        InlineKeyboardButton(text='Explain', callback_data='explain'),
        InlineKeyboardButton(text='Rus', callback_data='rus'),
    ]

    keyboard = InlineKeyboardMarkup(row_width=5, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


async def on_startup(dp: Dispatcher):
    await bot.delete_webhook()
    await dp.skip_updates()
    await users_db.create_users_database()
    await users_db.add_new_user(Config.ADMIN_ID)

    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await bot.send_message(chat_id=Config.ADMIN_ID, text="<b>Bot in Your Power, My Lord...</b>")


@dp.message_handler(commands='start')
async def start(message: Message):
    await users_db.add_new_user(message.from_user.id)
    await message.answer("Hey! I'm tele-xkcd-bot. [¬º-°]¬\n")
    await asyncio.sleep(1)
    await message.answer(help_text)


@dp.message_handler(commands='help')
async def help_func(message: Message):
    await message.answer(help_text)


async def mod_answer(user_id: int, data: dict):
    comic_id, title, img_url, comment, public_date = data.values()
    link = 'https://xkcd.com/' + str(comic_id)
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"

    await bot.send_message(chat_id=user_id,
                           text=headline,
                           disable_web_page_preview=True)
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
                             photo=InputFile('no_image.jpeg'),
                             disable_notification=True)
    await bot.send_message(chat_id=user_id,
                           text=f"<i>{comment.replace('<', '').replace('>', '')}</i>",
                           reply_markup=get_keyboard(),
                           disable_web_page_preview=True,
                           disable_notification=True)

    if comic_id in specific_comic_ids:
        await bot.send_message(chat_id=user_id,
                               text=f"It's peculiar comic!:D It's preferable to view it "
                                    f"in <a href='{link}'>your browser</a>.",
                               disable_web_page_preview=True,
                               disable_notification=True)


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

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
    comic_data = await comics_db.get_comic_data_by_id(new_comic_id)
    await mod_answer(call.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('rus'))
async def rus_version(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    comic_data = await comics_db.get_rus_version_data(current_comic_id)
    if not list(comic_data.values())[1]:
        await call.message.answer_photo(photo=InputFile('no_translation.jpg'),
                                        reply_markup=get_keyboard())
    else:
        await mod_answer(call.from_user.id, data=comic_data)


# TODO: implement keyboard
@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    text, url = parser.get_explanation(current_comic_id)
    text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    await call.message.answer(text=text,
                              reply_markup=get_keyboard(),
                              disable_web_page_preview=True)


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text

    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await message.answer(f'Please, write a number (1 - {latest})!')
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_user_current_comic(message.from_user.id, comic_id)
            await mod_answer(message.from_user.id, data=comic_data)
    else:
        title = user_input
        comic_data = await comics_db.get_comic_data_by_title(title)
        if not comic_data:
            await message.answer(f"There's no this title!")
        else:
            await users_db.update_user_current_comic(message.from_user.id, comic_data.get('comic_id'))
            await mod_answer(message.from_user.id, data=comic_data)


# TODO: implement bookmarking and FSM
@dp.callback_query_handler(Text('bookmark'))
async def bookmark(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    pass


# TODO: implement getting all users
def get_users():
    all_users_ids = 0
    for user_id in (Config.ADMIN_ID,):
        yield user_id


async def check_last_comic():
    current_db_last_comic_id = await comics_db.get_last_comic_id()
    real_current_last_comic_id = parser.get_and_update_latest_comic_id()

    if real_current_last_comic_id > current_db_last_comic_id:
        for id in range(current_db_last_comic_id+1, real_current_last_comic_id+1):
            data = parser.get_full_comic_data(id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            for user_id in get_users():
                await bot.send_message(user_id, "<b>Here\'s new comic!</b>")
                comic_data = await comics_db.get_comic_data_by_id(real_current_last_comic_id)
                await mod_answer(user_id, data=comic_data)
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            print(f"{count} messages successful sent.")  # TODO: add to log?


def repeat(coro, loop):
    delay = 60 * 25
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == "__main__":
    loop.call_later(5, repeat, check_last_comic, loop)
    if Config.HEROKU:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            # on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT,
        )
    else:
        start_polling(dp, on_startup=on_startup)
