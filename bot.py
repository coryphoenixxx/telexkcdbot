import asyncio

from random import randint
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from parser_ import Parser
from config_ import Config
from database_ import ComicsDatabase, UsersDatabase


loop = asyncio.get_event_loop()
bot = Bot(Config.API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())


WEBHOOK_HOST = f'https://{Config.HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{Config.API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_HOST = '0.0.0.0'
PORT = Config.PORT


parser = Parser()
users_db = UsersDatabase()
comics_db = ComicsDatabase()


help_text = """
<b>Here is my list of commands</b>:
 Type in the <u><b>comic number</b></u> and I'll find it for you!
 Type in the <u><b>comic title</b></u> and I'll try to find it for you!
 
 <b>/subscribe</b> - I'll notify you whenever a new xkcd comics is released.
 <b>/unsubscribe</b> - I'll stop notifying you when a new xkcd comics are released.
 <b>/bookmarks</b> - I'll send you your bookmarks.
 
 <b>/help</b> - I'll send you this text.
 """


def common_comic_keyboard():
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


def stop_next_keyboard():
    buttons = [
        InlineKeyboardButton(text='Bookmark\u2606', callback_data='rl_bookmark'),
        InlineKeyboardButton(text='Explain', callback_data='rl_explain'),
        InlineKeyboardButton(text='Rus', callback_data='rl_rus'),
        InlineKeyboardButton(text='Stop', callback_data='stop'),
        InlineKeyboardButton(text='Next>', callback_data='go_next')
    ]

    keyboard = InlineKeyboardMarkup(row_width=3, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


async def on_startup(dp: Dispatcher):
    await bot.delete_webhook()
    await users_db.create_users_database()
    await users_db.add_new_user(Config.ADMIN_ID)
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await bot.send_message(chat_id=Config.ADMIN_ID, text="<b>I'm here, in Your Power, My Lord...</b>")


async def on_shutdown(dp: Dispatcher):
    await bot.send_message(chat_id=Config.ADMIN_ID, text="<b>Something killed Your squire, My Lord...</b>")


async def mod_answer(user_id: int, data: dict, keyboard=common_comic_keyboard):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data.values()

    url = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'
    headline = f"<b>{comic_id}. \"<a href='{url}'>{title}</a>\"</b>   <i>({public_date})</i>"

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
                             photo=InputFile('static/no_image.png'),
                             disable_notification=True)
    await bot.send_message(chat_id=user_id,
                           text=f"<i>{comment.replace('<', '').replace('>', '')}</i>",  # for comment with tags
                           reply_markup=keyboard(),
                           disable_web_page_preview=True,
                           disable_notification=True)

    if is_specific:
        await asyncio.sleep(1)
        await bot.send_message(chat_id=user_id,
                               text=f"It's a peculiar comic! ^^ It's preferable to view it "
                                    f"in <a href='{url}'>your browser</a>.",
                               disable_web_page_preview=True,
                               disable_notification=True)


@dp.message_handler(CommandStart())
async def start(message: Message):
    await users_db.add_new_user(message.from_user.id)
    bot_name = (await bot.me).username
    await message.answer(f"Hey! I'm {bot_name}.\n[¬º-°]¬\n")
    await asyncio.sleep(1)
    await message.answer(help_text)
    await asyncio.sleep(1)
    comic_data = await comics_db.get_comic_data_by_id(1)
    await users_db.update_user_current_comic(message.from_user.id, 1)
    await mod_answer(message.from_user.id, data=comic_data)


@dp.message_handler(commands='help')
async def help_func(message: Message):
    await message.answer(help_text)


# TODO: implement
@dp.message_handler(commands=('subscribe', 'unsubscribe'))
async def subscribe(message: Message):
    pass


@dp.callback_query_handler(Text(startswith='nav_'))
async def nav(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)

    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    action = call.data.split('_')[1]
    latest = parser.latest_comic_id

    actions = {
        'first': 1,
        'prev': current_comic_id - 1,
        'random': randint(1, latest),
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
async def rus_version(call: CallbackQuery, keyboard=common_comic_keyboard):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    comic_data = await comics_db.get_rus_version_data(current_comic_id)
    if not list(comic_data.values())[1]:
        await call.message.answer_photo(photo=InputFile('static/no_translation.png'),  # TODO: change
                                        reply_markup=keyboard())
    else:
        await mod_answer(call.from_user.id, data=comic_data)


@dp.callback_query_handler(Text('rl_rus'))
async def rl_rus_version(call: CallbackQuery):
    await rus_version(call, keyboard=stop_next_keyboard)


@dp.callback_query_handler(Text('explain'))
async def explanation(call: CallbackQuery, keyboard=common_comic_keyboard):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    current_comic_id = await users_db.get_user_current_comic(call.from_user.id)
    text, url = await parser.get_explanation(current_comic_id)
    text = f"{text}...<i><b><a href='{url}'>\n[continue]</a></b></i>"
    await call.message.answer(text=text,
                              reply_markup=keyboard(),
                              disable_web_page_preview=True)


@dp.callback_query_handler(Text('rl_explain'))
async def rl_explanation(call: CallbackQuery):
    await explanation(call, keyboard=stop_next_keyboard)


# TODO: implement bookmarking and FSM
@dp.callback_query_handler(Text('bookmark'))
async def bookmark(call: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id)
    pass


@dp.callback_query_handler(Text('stop'))
async def stop_func(call: CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                        message_id=call.message.message_id,
                                        reply_markup=common_comic_keyboard())
    await state.reset_data()


@dp.callback_query_handler(Text('go_next'))
async def go_next(call: CallbackQuery, state: FSMContext):
    try:
        comic_iter = (await state.get_data())['comic_iter']
        comic_data = next(comic_iter)
    except KeyError:
        pass
    except StopIteration:
        await stop_func(call, state)
    else:
        await state.update_data(comic_iter=comic_iter)
        await mod_answer(call.from_user.id, data=comic_data, keyboard=stop_next_keyboard)


@dp.message_handler()
async def echo(message: Message, state: FSMContext):
    user_input = message.text.lower()
    if user_input.isdigit():
        latest = parser.latest_comic_id
        comic_id = int(user_input)
        if (comic_id > latest) or (comic_id <= 0):
            await message.answer(f"Please, write a number (1 - {latest})!")
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await users_db.update_user_current_comic(message.from_user.id, comic_id)
            await mod_answer(message.from_user.id, data=comic_data)
    else:
        comic_list = await comics_db.get_comics_by_title(user_input)
        if not comic_list:
            await message.answer(f"There's no such comic title!")
        else:
            len_ = len(comic_list)
            if len_ >= 2:
                comic_iter = iter(comic_list)
                await message.answer(f"I found <u><b>{len_}</b></u> xkcd comics with word "
                                     f"<b>\"{user_input}\"</b> in their titles."
                                     f"\nHere\'s last by time:")
                await state.update_data(comic_iter=comic_iter)
                await go_next(message, state)
            elif len_ == 1:
                await message.answer(f"I found one:")
                await mod_answer(message.from_user.id, data=comic_list[0])


async def check_last_comic():
    async def get_subscribed_users():
        subscribed_users = await users_db.get_subscribed_users()
        for user_id in subscribed_users:
            yield user_id

    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = parser.get_and_update_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for id in range(db_last_comic_id+1, real_last_comic_id+1):
            data = parser.get_full_comic_data(id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            async for user_id in get_subscribed_users():
                await bot.send_message(user_id, "<b>And here\'s new comic!</b>")
                comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
                await mod_answer(user_id, data=comic_data)
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            print(f"{count} messages successful sent.")  # TODO: add to log?


if __name__ == "__main__":
    def repeat(coro, loop):
        delay = 60 * 0.5
        asyncio.ensure_future(coro(), loop=loop)
        loop.call_later(delay, repeat, coro, loop)

    loop.call_later(0, repeat, check_last_comic, loop)
    if Config.HEROKU:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT,
        )
    else:
        start_polling(dispatcher=dp,
                      skip_updates=True,
                      on_startup=on_startup,
                      on_shutdown=on_shutdown)


