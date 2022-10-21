from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InputFile, Message
from api_client import api
from common_utils import preprocess_text, remove_prev_message_kb
from config import IMG_DIR
from handlers.handlers_utils import (
    States,
    flip_next,
    is_cyrillic,
    rate_limit,
    send_bookmarks,
    send_comic,
    send_headlines_as_text,
    send_menu,
)
from keyboards import kboard
from middlewares.localization import _


@rate_limit(3, "start")
async def cmd_start(msg: Message, state: FSMContext) -> None:
    await remove_prev_message_kb(msg, state)
    await api.add_user(msg.from_user.id)

    await msg.answer(
        "<b>Select language | Выберите язык</b>",
        reply_markup=await kboard.lang_selection(),
    )
    await States.language_selection.set()


@rate_limit(3, "menu")
async def cmd_menu(msg: Message, state: FSMContext) -> None:
    await remove_prev_message_kb(msg, state)

    await send_menu(msg.from_user.id)


@rate_limit(3, "bookmarks")
async def cmd_bookmarks(msg: Message, state: FSMContext) -> None:
    await remove_prev_message_kb(msg, state)

    await send_bookmarks(
        user_id=msg.from_user.id,
        message_id=msg.message_id,
        msg_text=msg.text,
        state=state,
        keyboard=await kboard.menu_or_xkcding(msg.from_user.id),
    )


@rate_limit(2)
async def process_user_typing(msg: Message, state: FSMContext) -> None:
    await remove_prev_message_kb(msg, state)

    user_input = preprocess_text(msg.text)

    if not user_input:
        await msg.reply(
            _(
                "❗ <b>You did it. You broke my search engine.\n"
                "You can be proud of yourself!\n"
                "Here's your award:</b>"
            )
        )
        await msg.answer_photo(
            InputFile(IMG_DIR / "candy.jpg"),
            reply_markup=await kboard.menu_or_xkcding(msg.from_user.id),
        )

    elif user_input.isdigit():
        comic_id = int(user_input)
        last_comic_id = await api.get_latest_comic_id()

        if (comic_id > last_comic_id) or (comic_id <= 0):
            await msg.reply(
                _("❗ <b>Please, enter a number from 1 to {}!</b>").format(last_comic_id),
                reply_markup=await kboard.menu_or_xkcding(msg.from_user.id),
            )
        else:
            await send_comic(msg.from_user.id, comic_id=comic_id)

    else:
        if len(user_input) == 1:
            await msg.reply(_("❗ <b>I think there's no necessity to search by one character!</b>"))
        else:
            # What language the comics will be searched in and showed in flipping mode
            lang = "ru" if is_cyrillic(user_input) else "en"

            await state.update_data(fsm_lang=lang)

            comics_found_list = await api.get_comics_headlines_by_title(title=user_input, lang=lang)

            if not comics_found_list:
                await msg.reply(
                    _("❗ <b>There's no such comic title or command!</b>"),
                    reply_markup=await kboard.menu_or_xkcding(msg.from_user.id),
                )
            else:
                comics_found_num = len(comics_found_list)

                if comics_found_num == 1:
                    await msg.reply(_("❗ <b>I found one:</b>"))
                    comic_id = comics_found_list[0].comic_id
                    await send_comic(msg.from_user.id, comic_id=comic_id, comic_lang=lang)
                else:
                    comics_ids = [headline.comic_id for headline in comics_found_list]
                    await state.update_data(fsm_list=comics_ids)

                    await msg.reply(_("❗ <b>I found <u><b>{}</b></u> comics:</b>").format(comics_found_num))
                    await send_headlines_as_text(msg.from_user.id, headlines_info=comics_found_list)

                    await msg.answer(_("❗ <b>Now you can flip through the comics:</b>"))
                    await flip_next(msg.from_user.id, state)


def register_default_commands(dp: Dispatcher) -> None:
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_message_handler(cmd_menu, commands=["menu", "help"])
    dp.register_message_handler(cmd_bookmarks, commands=["bookmarks"])
    dp.register_message_handler(process_user_typing)
