import asyncio

from string import ascii_letters, digits
from typing import Tuple, Union
from dataclasses import astuple

from aiogram.types import InputFile, ChatActions
from aiogram.utils.exceptions import BadRequest, InvalidHTTPUrlContent, BotBlocked, UserDeactivated, ChatNotFound

from src.telexkcdbot.bot import bot
from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.config import ADMIN_ID
from src.telexkcdbot.keyboards import kboard
from src.telexkcdbot.paths import IMG_PATH, BASE_DIR
from src.telexkcdbot.logger import logger
from src.telexkcdbot.databases.comics_db import comics_db


cyrillic = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
punctuation = ' -(),.:;!?#+'


async def make_headline(comic_id: int, title: str, img_url: str, public_date: str = '') -> str:
    if 'http' not in img_url:
        link = title
    else:
        url = f'https://xkcd.com/{comic_id}' if comic_id != 880 \
                                             else 'https://xk3d.xkcd.com/880/'  # Original link is incorrect
        link = f"<a href='{url}'>{title}</a>"

    if public_date:
        return f"<b>{str(comic_id)}. \"{link}\"</b>   <i>({public_date})</i>"
    return f"<b>{str(comic_id) + '.':7}</b>\"{link}\""


async def send_comic(user_id: int, comic_id: int, keyboard=kboard.navigation, comic_lang: str = 'en'):
    comic_data = await comics_db.get_comic_data_by_id(comic_id, comic_lang)

    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific,
     has_ru_translation) = astuple(comic_data)

    await users_db.update_cur_comic_info(user_id, comic_id, comic_lang)

    headline = await make_headline(comic_id, title, img_url, public_date)

    await bot.send_message(user_id, headline, disable_web_page_preview=True, disable_notification=True)

    if is_specific:
        await bot.send_message(user_id,
                               text="❗❗❗ <b>This comic is peculiar!\nIt's preferable to view it in your browser.</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)

    try:
        if 'http' not in img_url:
            local_img = InputFile(BASE_DIR.joinpath(img_url))
            if img_url.endswith('.gif'):
                await bot.send_animation(user_id, animation=local_img, disable_notification=True)
            else:
                await bot.send_photo(user_id, photo=local_img, disable_notification=True)
        elif img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, animation=img_url, disable_notification=True)
        else:
            await bot.send_photo(user_id,
                                 photo=InputFile(IMG_PATH.joinpath('no_image.png')),
                                 disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest) as err:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>Couldn't get image. Press on title to view comic in your browser!</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)
        logger.error(f"Couldn't send {comic_id} to {user_id} comic! {err}")

    await bot.send_message(user_id,
                           text=f"<i>{comment}</i>",
                           disable_web_page_preview=True,
                           disable_notification=True,
                           reply_markup=await keyboard(user_id, comic_data, comic_lang))


async def preprocess_text(text: str) -> str:
    permitted = ascii_letters + digits + cyrillic + punctuation
    processed_text = ''.join([ch for ch in text.strip() if ch in permitted])[:30]
    return processed_text


async def broadcast(text: str, comic_id: Union[int, None] = None):  # Make Optional
    count = 0
    all_users_ids = await users_db.get_all_users_ids()  # Uses for delete users
    subscribed_users = await users_db.get_subscribed_users()

    try:
        for user_id in all_users_ids:
            try:
                await bot.send_chat_action(user_id, ChatActions.TYPING)
            except (BotBlocked, UserDeactivated, ChatNotFound):
                await users_db.delete_user(user_id)
            else:
                if user_id in subscribed_users:
                    await bot.send_message(user_id, text=text, disable_notification=True)
                    if comic_id:
                        await send_comic(user_id, comic_id=comic_id)
                    count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
    except Exception as err:
        logger.error(f"Couldn't broadcast on count {count}!", err)
    finally:
        await bot.send_message(ADMIN_ID, f"❗ <b>{count}/{len(subscribed_users)} messages were successfully sent.</b>")
        logger.info(f"{count}/{len(subscribed_users)} messages were successfully sent")
