import asyncio

from aiogram import Dispatcher
from aiogram.types import Message, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from contextlib import suppress

from src.bot.loader import comics_db, users_db, bot
from src.bot.utils import preprocess_text
from src.bot.handlers.utils import (is_cyrillic, send_comics_list_text_in_bunches, suppress_exceptions,
                                    send_menu, send_user_bookmarks, trav_step, rate_limit, send_comic)
from src.bot.keyboards import kboard
from src.bot.paths import IMG_PATH


@rate_limit(2)
async def cmd_start(msg: Message, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await users_db.add_user(msg.from_user.id)
    await msg.answer(f"<b>❗ The <u>{(await bot.me).username}</u> at your disposal!</b>")
    await msg.answer_photo(InputFile(IMG_PATH.joinpath('bot_image.png')))
    await asyncio.sleep(2)
    await send_menu(msg.from_user.id)


@rate_limit(2)
async def cmd_menu(msg: Message, state: FSMContext):
    await state.reset_data()
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await send_menu(msg.from_user.id)


async def cmd_bookmarks(msg: Message, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)

    await send_user_bookmarks(msg.from_user.id, msg.message_id, state)


@rate_limit(1)
async def process_user_typing(msg: Message, state: FSMContext):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)
    await state.reset_data()

    # TODO: а что если в названии цифра?

    user_input = await preprocess_text(msg.text)

    if user_input.isdigit():
        comic_id = int(user_input)
        latest = await comics_db.get_last_comic_id()

        if (comic_id > latest) or (comic_id <= 0):
            await msg.reply(f"❗❗❗\n<b>Please, enter a number between 1 and {latest}!</b>",
                            reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
        else:
            comic_data = await comics_db.get_comic_data_by_id(comic_id)
            await send_comic(msg.from_user.id, comic_data=comic_data)
    else:
        if len(user_input) == 1:
            await msg.reply(f"❗ <b>I think there's no necessity to search by one character!)</b>")
        else:
            if await is_cyrillic(user_input):
                lang = 'ru'
                await state.update_data(lang='ru')
            else:
                lang = 'en'

            found_comics_list = await comics_db.get_comics_info_by_title(user_input, lang=lang)

            if not found_comics_list:
                await msg.reply(f"❗❗❗\n<b>There's no such comic title or command!</b>",
                                reply_markup=await kboard.menu_or_xkcding(msg.from_user.id))
            else:
                found_comics_num = len(found_comics_list[0])

                if found_comics_num == 1:
                    await msg.reply(f"❗ <b>I found one:</b>")
                    comic_id = found_comics_list[0][0]
                    comic_data = await comics_db.get_comic_data_by_id(comic_id, comic_lang=lang)
                    await send_comic(msg.from_user.id, comic_data=comic_data, comic_lang=lang)

                elif found_comics_num >= 2:
                    comics_ids, _, _ = found_comics_list
                    await msg.reply(f"❗ <b>I found <u><b>{found_comics_num}</b></u> comics:</b>")
                    await send_comics_list_text_in_bunches(msg.from_user.id, found_comics_list, lang)
                    await state.update_data(list=list(comics_ids))
                    await trav_step(msg.from_user.id, msg.message_id, state)


def register_default_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_message_handler(cmd_menu, commands=['menu', 'help'])
    dp.register_message_handler(cmd_bookmarks, commands=['bookmarks'])
    dp.register_message_handler(process_user_typing)
