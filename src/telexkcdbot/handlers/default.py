import asyncio

from aiogram import Dispatcher
from aiogram.types import Message, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart

from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import preprocess_text
from src.telexkcdbot.handlers.handlers_utils import (is_cyrillic, send_headlines_as_text, remove_kb_of_prev_message,
                                                     send_menu, send_user_bookmarks, trav_step, rate_limit, send_comic)
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.paths import IMG_PATH


@rate_limit(2)
async def cmd_start(msg: Message, state: FSMContext):
    await state.reset_data()
    await remove_kb_of_prev_message(msg)

    await users_db.add_user(msg.from_user.id)
    await msg.answer(f"<b>❗ The <u>telexkcdbot</u> at your disposal!</b>")
    await msg.answer_photo(InputFile(IMG_PATH.joinpath('bot_image.png')))
    await asyncio.sleep(2)
    await send_menu(msg.from_user.id)


@rate_limit(2)
async def cmd_menu(msg: Message, state: FSMContext):
    await state.reset_data()
    await remove_kb_of_prev_message(msg)
    await send_menu(msg.from_user.id)


async def cmd_bookmarks(msg: Message, state: FSMContext):
    await remove_kb_of_prev_message(msg)
    await send_user_bookmarks(msg.from_user.id, msg.message_id, state)


@rate_limit(1)
async def process_user_typing(msg: Message, state: FSMContext):
    await remove_kb_of_prev_message(msg)
    await state.reset_data()

    user_input = await preprocess_text(msg.text)

    # TODO: что если номер в названии?

    if user_input.isdigit():
        comic_id = int(user_input)
        latest = await comics_db.get_last_comic_id()

        if (comic_id > latest) or (comic_id <= 0):
            await msg.reply(f"❗❗❗\n<b>Please, enter a number from 1 to {latest}!</b>",
                            reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
        else:
            await send_comic(msg.from_user.id, comic_id=comic_id)
    else:
        if len(user_input) == 1:
            await msg.reply(f"❗ <b>I think there's no necessity to search by one character!)</b>")
        else:
            if await is_cyrillic(user_input):
                lang = 'ru'
                await state.update_data(lang='ru')
            else:
                lang = 'en'

            found_comics_list = await comics_db.get_comics_headlines_info_by_title(user_input, lang=lang)

            if not found_comics_list:
                await msg.reply(f"❗❗❗\n<b>There's no such comic title or command!</b>",
                                reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
            else:
                found_comics_num = len(found_comics_list)

                if found_comics_num == 1:
                    print(found_comics_list)
                    await msg.reply(f"❗ <b>I found one:</b>")
                    comic_id = found_comics_list[0].comic_id
                    await send_comic(msg.from_user.id, comic_id=comic_id, comic_lang=lang)
                else:
                    comics_ids = [headline.comic_id for headline in found_comics_list]
                    await msg.reply(f"❗ <b>I found <u><b>{found_comics_num}</b></u> comics:</b>")
                    await send_headlines_as_text(msg.from_user.id, headlines_info=found_comics_list)
                    await state.update_data(list=list(comics_ids))
                    await trav_step(msg.from_user.id, msg.message_id, state)


def register_default_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_message_handler(cmd_menu, commands=['menu', 'help'])
    dp.register_message_handler(cmd_bookmarks, commands=['bookmarks'])
    dp.register_message_handler(process_user_typing)
