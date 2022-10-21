import asyncio
from contextlib import suppress
from dataclasses import astuple
from string import ascii_letters, digits
from typing import Callable, Generator, Optional

from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions, InputFile, Message
from aiogram.utils.exceptions import (
    BadRequest,
    BotBlocked,
    ChatNotFound,
    InvalidHTTPUrlContent,
    MessageCantBeEdited,
    MessageNotModified,
    MessageToEditNotFound,
    UserDeactivated,
)
from api_client import api
from bot import bot
from comic_data_getter import comics_data_getter
from config import ADMIN_ID, IMG_DIR, RU_COMIC_DATA_DIR
from keyboards import kboard
from loguru import logger
from middlewares.localization import _, localization

suppressed_exceptions = (
    AttributeError,
    MessageNotModified,
    MessageToEditNotFound,
    MessageCantBeEdited,
)
cyrillic = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
punctuation = " -(),.:;!?#+*/"


def make_headline(comic_id: int, title: str, img_url: str, public_date: Optional[str] = None) -> str:
    """
    Makes the headline string like <number>. <title> and optional <public date>.
    Don't add public date and aligns the text a little for flipping mode.
    """

    if "http" not in img_url:  # If it's local storage russian comic image don't make link
        link = title
    else:
        url = (
            f"https://xkcd.com/{comic_id}" if comic_id != 880 else "https://xk3d.xkcd.com/880/"
        )  # Original link is incorrect
        link = f"<a href='{url}'>{title}</a>"

    if public_date:
        return f'<b>{str(comic_id)}. "{link}"</b>   <i>({public_date})</i>'
    return f"<b>{str(comic_id) + '.':7}</b>\"{link}\""


async def send_comic(
    user_id: int,
    comic_id: int,
    keyboard: Callable = kboard.navigation,
    comic_lang: str = "en",
    from_toggle_lang_cb: bool = False,
    from_broadcast: bool = False,
) -> None:
    """
    :param user_id:
    :param comic_id:
    :param keyboard:
    :param comic_lang: In what language to send the comic
    :param from_toggle_lang_cb: Uses for correct defining in what language to send the comic
    :param from_broadcast: User for correct defining in what language send user keyboard
    :return:
    """
    user_lang = await api.get_user_lang(user_id)

    # Fix bug with incorrect keyboard language in broadcasting
    if from_broadcast:
        await localization.set_user_locale(user_lang)

    # Changes the language of the comic to Russian if possible
    if user_lang == "ru":
        ru_ids = comics_data_getter.ru_comics_ids
        if comic_id in ru_ids:
            (
                last_comic_id,
                last_comic_lang,
            ) = await api.get_last_comic_info(user_id)
            if last_comic_id == comic_id and last_comic_lang == "ru" and from_toggle_lang_cb:
                comic_lang = "en"
            else:
                comic_lang = "ru"

    await api.update_last_comic_info(user_id, comic_id, comic_lang)

    comic_data = await api.get_comic_data_by_id(comic_id, comic_lang)
    (
        comic_id,
        title,
        img_url,
        comment,
        public_date,
        is_specific,
        has_ru_translation,
    ) = astuple(comic_data)

    headline = make_headline(comic_id, title, img_url, public_date)

    await bot.send_message(
        user_id,
        headline,
        disable_web_page_preview=True,
        disable_notification=True,
    )

    if is_specific:
        await bot.send_message(
            user_id,
            text=_("❗ <b>This comic is special!\n" "Better to view it in your browser.</b>"),
            disable_web_page_preview=True,
            disable_notification=True,
        )

    # Sends the comic image
    try:
        if "http" not in img_url:  # Russian comics saved locally
            local_img = InputFile(RU_COMIC_DATA_DIR / img_url)
            await bot.send_photo(user_id, photo=local_img, disable_notification=True)
        elif img_url.endswith((".png", ".jpg", ".jpeg")):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith(".gif"):
            await bot.send_animation(user_id, animation=img_url, disable_notification=True)
        else:
            # Some comics haven't image
            await bot.send_photo(
                user_id,
                photo=InputFile(IMG_DIR / "no_image.png"),
                disable_notification=True,
            )
    except (InvalidHTTPUrlContent, BadRequest) as err:
        await bot.send_message(
            user_id,
            text=_("❗ <b>Couldn't get image. Press on title to view comic in your browser!</b>"),
            disable_web_page_preview=True,
            disable_notification=True,
        )
        logger.error(f"Couldn't send {comic_id} image to {user_id} comic: {err}")

    # Sends the Randall Munroe's comment
    await bot.send_message(
        user_id,
        text=f"<i>{comment}</i>",
        disable_web_page_preview=True,
        disable_notification=True,
        reply_markup=await keyboard(user_id, comic_data, comic_lang),
    )


async def broadcast(msg_text: Optional[str] = None, comic_id: Optional[int] = None) -> None:
    """Sends to users a new comic or an admin message"""
    # TODO: fix looping
    # TODO: separate logic
    count = 0
    all_users_ids = await api.get_all_users_ids()

    try:
        for user_id in all_users_ids:
            if await user_is_unavailable(user_id):
                await api.delete_user(user_id)
            else:
                user_lang = await api.get_user_lang(user_id)

                # For sending comic
                if comic_id:
                    only_ru_mode = await api.get_only_ru_mode_status(user_id)
                    if not only_ru_mode:  # In only-ru mode users don't get a new English comic
                        notification_sound = await api.get_notification_sound_status(user_id)

                        text = (
                            "🔥 <b>And here comes the new comic!</b> 🔥"
                            if user_lang == "en"
                            else "🔥 <b>А вот и свежий выпуск!</b> 🔥"
                        )

                        if notification_sound:
                            msg = await bot.send_message(user_id, text=text)
                        else:
                            msg = await bot.send_message(user_id, text=text, disable_notification=True)

                        # Try to remove a keyboard of a previous message
                        with suppress(*suppressed_exceptions):
                            await bot.edit_message_reply_markup(user_id, msg.message_id - 1)

                        await send_comic(user_id, comic_id=comic_id, from_broadcast=True)

                        count += 1
                # For sending admin message
                else:
                    title_text = (
                        "❗ <u><b>ADMIN MESSAGE:</b></u>\n"
                        if user_lang == "en"
                        else "❗ <u><b>СООБЩЕНИЕ ОТ АДМИНА:</b></u>\n"
                    )
                    text = title_text + str(msg_text)

                    await bot.send_message(user_id, text=text, disable_notification=True)

                    count += 1

                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Telegram limit: 30 messages per second)

    except Exception as err:
        logger.error(f"Couldn't broadcast on count {count}!", err)
    finally:
        broadcast_final_text = f"{count}/{len(all_users_ids)} messages were successfully sent."
        await bot.send_message(
            ADMIN_ID,
            text=f"❗ <b>{broadcast_final_text}</b>",
            disable_notification=True,
        )
        logger.info(broadcast_final_text)


async def remove_prev_message_kb(msg: Message, state: Optional[FSMContext] = None) -> None:
    if state:
        await state.reset_data()
    with suppress(*suppressed_exceptions):
        await bot.edit_message_reply_markup(msg.from_user.id, msg.message_id - 1)


def cut_into_chunks(lst: list, chunk_size: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


def preprocess_text(text: str) -> str:
    """Removes danger symbols from the text for before logging or searching"""

    permitted = ascii_letters + digits + cyrillic + punctuation
    processed_text = "".join([ch for ch in text.strip() if ch in permitted])[:30]
    return processed_text


async def user_is_unavailable(user_id: int) -> bool:
    try:
        await bot.send_chat_action(user_id, ChatActions.TYPING)
    except (BotBlocked, UserDeactivated, ChatNotFound):
        return True
    return False
