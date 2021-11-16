import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound, MessageCantBeEdited
from aiogram.types import Message, CallbackQuery
from contextlib import suppress
from typing import Callable, Generator

from src.telexkcdbot.bot import bot
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.databases.comics_db import comics_db
from src.telexkcdbot.common_utils import send_comic, cyrillic, punctuation, make_headline
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.databases.models import ComicHeadlineInfo


suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


def cut_into_chunks(lst: list, n: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def remove_prev_message_kb(msg: Message):
    with suppress(*suppress_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)


async def remove_callback_kb(call: CallbackQuery):
    with suppress(*suppress_exceptions):
        await call.message.edit_reply_markup()


def is_cyrillic(text: str) -> bool:
    return set(text).issubset(cyrillic + punctuation)


async def send_headlines_as_text(user_id: int, headlines_info: list[ComicHeadlineInfo]):
    for chunk in cut_into_chunks(headlines_info, 35):
        headlines = []
        for headline_info in chunk:
            headlines.append(await make_headline(comic_id=headline_info.comic_id,
                                                 title=headline_info.title,
                                                 img_url=headline_info.img_url))
        text = '\n'.join(headlines)
        await bot.send_message(user_id, text, disable_web_page_preview=True)
        await asyncio.sleep(1)


async def send_bookmarks(user_id: int, state: FSMContext, keyboard: Callable = None):
    bookmarks = await users_db.get_bookmarks(user_id)

    if not bookmarks:
        text = f"❗ <b>You have no bookmarks.\nYou can bookmark a comic with the ❤ press.</b>"
        if keyboard:
            await bot.send_message(user_id, text, reply_markup=keyboard)
        else:
            await bot.send_message(user_id, text, reply_markup=await kboard.menu_or_xkcding(user_id))
    elif len(bookmarks) == 1:
        await bot.send_message(user_id, f"❗ <b>You have one:</b>")
        await send_comic(user_id, comic_id=bookmarks[0])
    else:
        await bot.send_message(user_id, f"❗ <b>You have <u><b>{len(bookmarks)}</b></u> bookmarks:</b>")
        headlines_info = await comics_db.get_comics_headlines_info_by_ids(bookmarks)
        await send_headlines_as_text(user_id, headlines_info=headlines_info)
        await state.update_data(fsm_list=bookmarks)
        await trav_step(user_id, state)


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


async def trav_step(user_id: int, state: FSMContext):
    fsm_list = (await state.get_data()).get('fsm_list')
    fsm_lang = (await state.get_data()).get('fsm_lang')
    comic_lang = 'en' if not fsm_lang else fsm_lang

    comic_id = fsm_list.pop(0)
    await state.update_data(fsm_list=fsm_list)

    if fsm_list:
        await send_comic(user_id, comic_id=comic_id, keyboard=kboard.traversal, comic_lang=comic_lang)
    else:
        await bot.send_message(user_id, text="❗ <b>The last one:</b>")
        await send_comic(user_id, comic_id=comic_id, keyboard=kboard.navigation, comic_lang=comic_lang)


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
