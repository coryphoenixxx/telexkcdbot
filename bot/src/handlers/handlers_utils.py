import asyncio
import random
from collections.abc import Callable
from contextlib import suppress
from typing import Any, TypeVar

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from src.api_client import api
from src.bot_instance import bot
from src.comic_data_getter import comics_data_getter
from src.common_utils import cut_into_chunks, cyrillic, make_headline, punctuation, send_comic, suppressed_exceptions
from src.keyboards import kboard
from src.middlewares.localization import _
from src.models import ComicHeadlineInfo

F = TypeVar("F", bound=Callable[..., Any])


class States(StatesGroup):
    language_selection = State()
    typing_admin_broadcast_msg = State()
    typing_msg_to_admin = State()
    typing_admin_support_answer = State()
    waiting = State()


async def remove_callback_kb(call: CallbackQuery) -> None:
    with suppress(*suppressed_exceptions):
        await call.message.edit_reply_markup()


def is_cyrillic(text: str) -> bool:
    return set(text).issubset(cyrillic + punctuation)


async def send_headlines_as_text(user_id: int, headlines_info: list[ComicHeadlineInfo]) -> None:
    for chunk in cut_into_chunks(headlines_info, 35):
        headlines = []
        for headline_info in chunk:
            headlines.append(
                make_headline(
                    comic_id=headline_info.comic_id,
                    title=headline_info.title,
                    img_url=headline_info.img_url,
                ),
            )
        await bot.send_message(
            user_id,
            text="\n".join(headlines),
            disable_web_page_preview=True,
            disable_notification=True,
        )
        await asyncio.sleep(1)


async def send_bookmarks(
    user_id: int,
    message_id: int,
    msg_text: str,
    state: FSMContext,
    keyboard: InlineKeyboardMarkup,
) -> None:
    bookmarks = await api.get_bookmarks(user_id)

    if not bookmarks:
        if "❤" in msg_text:
            await bot.delete_message(user_id, message_id)
        text = _("❗ <b>You have no bookmarks.\nYou can bookmark a comic with the ❤ press.</b>")
        await bot.send_message(user_id, text, reply_markup=keyboard)
    elif len(bookmarks) == 1:
        await bot.send_message(user_id, _("❗ <b>You have one:</b>"))
        await send_comic(user_id, comic_id=bookmarks[0])
    else:
        await bot.send_message(
            user_id,
            _("❗ <b>You have <u><b>{}</b></u> bookmarks:</b>").format(len(bookmarks)),
        )
        headlines_info = await api.get_comics_headlines_by_ids(bookmarks)
        await send_headlines_as_text(user_id, headlines_info=headlines_info)
        await state.update_data(fsm_list=bookmarks)
        await flip_next(user_id, state)


async def send_menu(user_id: int) -> None:
    help_text = _(
        """<b>***** MENU *****</b>

• send me the <u><b>number</b></u>, and I'll find a comic with this number;
• send me the <u><b>word</b></u>, and I'll find comics whose titles contains this word.

<u><b>Menu options:</b></u>
• adjust the notification sound for the new comic release <i>(every Mon, Wed and Fri USA time)</i>;
• view comics from your bookmarks;
• remove language button <i>(under the comic, which have russian translation)</i> if you don't need it;
• contact admin.

____________________
""",
    )
    user_lang = await api.get_user_lang(user_id)
    users_num = len(await api.get_all_users_ids())
    ru_comics_num = len(comics_data_getter.ru_comics_ids)

    comic_num = len(await api.get_all_comics_ids())
    if user_lang == "en":
        stat_text = f"Comics: <b>{comic_num}</b>\n" f"Users: <b>{users_num}</b>\n"
    else:
        stat_text = (
            f"Комиксов: <b>{comic_num}</b>\n"
            f"Переводов: <b>{ru_comics_num}</b>\n"
            f"Пользователей: <b>{users_num}</b>\n"
        )

    await bot.send_message(
        user_id,
        text=help_text + stat_text,
        reply_markup=await kboard.menu(user_id),
        disable_notification=True,
    )


async def flip_next(user_id: int, state: FSMContext) -> None:
    """Handles flipping mode - when user views his bookmarks or found comics."""
    fsm_list = (await state.get_data()).get("fsm_list")

    if fsm_list:
        fsm_lang = (await state.get_data()).get("fsm_lang")
        comic_lang = fsm_lang if fsm_lang else "en"

        comic_id = fsm_list.pop(0)
        await state.update_data(fsm_list=fsm_list)

        if fsm_list:
            await send_comic(
                user_id,
                comic_id=comic_id,
                keyboard=kboard.flipping,
                comic_lang=comic_lang,
            )
        else:
            await bot.send_message(user_id, text=_("❗ <b>The last one:</b>"))
            await send_comic(
                user_id,
                comic_id=comic_id,
                keyboard=kboard.navigation,
                comic_lang=comic_lang,
            )
    else:
        # Bot uses a memory cache and sometimes reloaded, losing some data. Perfect crutch!
        await bot.send_message(
            user_id,
            text=_("❗ <b>Sorry, I was rebooted and forgot all the data... 😢\n" "Please repeat your request.</b>"),
            reply_markup=await kboard.menu_or_xkcding(user_id),
        )


async def calc_new_comic_id(user_id: int, comic_id: int, action: str) -> int:
    if action == "first":
        return 1

    only_ru_mode = await api.get_only_ru_mode_status(user_id)

    if only_ru_mode:
        ru_ids = sorted(comics_data_getter.ru_comics_ids)
        comic_id_by_action = {
            "prev": max(filter(lambda x: x < comic_id, ru_ids)) if comic_id > ru_ids[0] else ru_ids[-1],
            "random": random.choice(ru_ids),
            "next": min(filter(lambda x: x > comic_id, ru_ids)) if comic_id < ru_ids[-1] else ru_ids[0],
            "last": ru_ids[-1],
        }
    else:
        latest = await api.get_latest_comic_id()
        comic_id_by_action = {
            "prev": comic_id - 1 if comic_id - 1 >= 1 else latest,
            "random": random.randint(1, latest),
            "next": comic_id + 1 if comic_id + 1 <= latest else 1,
            "last": latest,
        }
    return comic_id_by_action[action]


def rate_limit(limit: int, key: str | None = None) -> Callable[[F], F]:
    """Decorator for configuring rate limit and key in different functions."""

    def decorator(func: F) -> F:
        func.throttling_rate_limit = limit
        if key:
            func.throttling_key = key
        return func

    return decorator


def is_explained_func(text: str) -> bool:
    # Don't show "Explain" button if explanation text already exists
    if "↪" in text:
        return True
    return False
