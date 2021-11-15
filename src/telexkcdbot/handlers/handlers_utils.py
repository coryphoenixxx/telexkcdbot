import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound, MessageCantBeEdited
from aiogram.types import Message
from contextlib import suppress
from typing import List
from dataclasses import astuple

from src.telexkcdbot.bot import bot
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import send_comic, cyrillic, punctuation, make_headline
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.models import ComicHeadlineInfo


suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


def cut_into_chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def remove_kb_of_prev_message(msg: Message):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)


async def is_cyrillic(text: str) -> bool:
    return set(text).issubset(cyrillic + punctuation)


async def send_headlines_as_text(user_id: int, headlines_info: List[ComicHeadlineInfo]):
    for chunk in cut_into_chunks(headlines_info, 35):
        headlines = []
        for headline_info in chunk:
            headlines.append(await make_headline(comic_id=headline_info.comic_id,
                                                 title=headline_info.title,
                                                 img_url=headline_info.img_url))
        text = '\n'.join(headlines)
        await bot.send_message(user_id, text, disable_web_page_preview=True)
        await asyncio.sleep(0.8)


async def send_user_bookmarks(user_id: int, message_id: int, state: FSMContext, keyboard=None):
    from pprint import pprint
    bookmarks = await users_db.get_bookmarks(user_id)

    if not bookmarks:
        text = f"❗ <b>You have no bookmarks.\nYou can bookmark a comic with the ❤ press.</b>"
        if keyboard:
            await bot.send_message(user_id, text, reply_markup=keyboard)
        else:
            await bot.send_message(user_id, text, reply_markup=await kboard.menu_or_xkcding(user_id))
    else:
        await bot.send_message(user_id, f"❗ <b>You have <u><b>{len(bookmarks)}</b></u> bookmarks</b>:")
        headlines_info = await comics_db.get_comics_headlines_info_by_ids(bookmarks)
        # pprint(headlines_info)
        await send_headlines_as_text(user_id, headlines_info=headlines_info)
        await state.update_data(list=bookmarks)

        await trav_step(user_id, message_id, state)


async def send_menu(user_id: int):
    help_text = """<b>*** MENU ***</b>

Type in the <u><b>number</b></u> and I'll find a comic with this number!
Type in the <u><b>word</b></u> and I'll find comics whose titles contains this word! 


<u><b>In menu you can:</b></u>
— subscribe for the new comic release <i>(every Mon, Wed and Fri USA time)</i>.
— read comics from your bookmarks.
— remove language button <i>(under the comic, which have russian translation)</i> if you don't need it.
— start xkcding!

If the sound of the notification annoys you, you can <b><u>mute</u></b> the telexkcdbot 
<i>(click on the three dots in the upper right corner)</i>.


❗❗❗
If something goes wrong or looks strange try to view a comic in your browser <i>(I'll give you a link)</i>."""

    await bot.send_message(user_id, help_text, reply_markup=await kboard.menu(user_id), disable_notification=True)


async def trav_step(user_id: int, message_id: int, state: FSMContext):
    list_ = (await state.get_data()).get('list')

    if not list_:
        await trav_stop(user_id, message_id, state)
    else:
        lang = (await state.get_data()).get('lang')
        comic_lang = 'en' if not lang else 'ru'

        if list_:
            await send_comic(user_id, comic_id=list_.pop(0), keyboard=kboard.traversal, comic_lang=comic_lang)
            await state.update_data(list=list_)
        else:
            await send_comic(user_id, comic_id=list_.pop(0), keyboard=kboard.navigation, comic_lang=comic_lang)
            await state.reset_data()


async def trav_stop(user_id: int, message_id: int, state: FSMContext):
    comic_id, comic_lang = await users_db.get_cur_comic_info(user_id)
    comic_data = await comics_db.get_comic_data_by_id(comic_id)
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(user_id,
                                            message_id=message_id,
                                            reply_markup=await kboard.navigation(user_id, comic_data, comic_lang))
    await state.reset_data()


def rate_limit(limit: int, key=None):
    """
    Decorator for configuring rate limit and key in different functions.
    """
    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func
    return decorator
