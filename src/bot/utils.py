import asyncio
from string import ascii_letters, digits
from typing import Tuple, Union
from aiogram.types import InputFile, ChatActions
from aiogram.utils.exceptions import BadRequest, InvalidHTTPUrlContent, BotBlocked, UserDeactivated, ChatNotFound

from src.bot.loader import bot, users_db
from src.bot.config import ADMIN_ID
from src.bot.keyboards import kboard
from src.bot.paths import IMG_PATH, BASE_DIR
from src.bot.logger import logger


cyrillic = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
punctuation = ' -(),.:;!?#+'


async def get_link(comic_id: int, title: str, img_url: str, comic_lang: str) -> str:
    if 'http' not in img_url:
        return title
    else:
        if comic_lang == 'ru':
            # TODO: переделать, мы больше не юзаем xkcd.su
            url = f'https://xkcd.su/{comic_id}'
        else:
            # Original image is broken
            url = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'
        return f"<a href='{url}'>{title}</a>"


async def send_comic(user_id: int, comic_data: tuple, keyboard=kboard.navigation, comic_lang: str = 'en'):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = comic_data

    await users_db.update_cur_comic_info(user_id, comic_id, comic_lang)

    link = await get_link(comic_id, title, img_url, comic_lang)
    headline = f"<b>{comic_id}. \"{link}\"</b>   <i>({public_date})</i>"

    await bot.send_message(user_id, headline, disable_web_page_preview=True, disable_notification=True)

    if is_specific:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>This comic is peculiar!\n"
                                    f"It's preferable to view it in your browser.</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)

    try:
        if 'http' not in img_url:
            local_img = InputFile(BASE_DIR.joinpath(img_url))
            await bot.send_photo(user_id, photo=local_img, disable_notification=True)
        elif img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, photo=img_url, disable_notification=True)
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
                           reply_markup=await keyboard(user_id, comic_id, comic_lang),
                           disable_web_page_preview=True,
                           disable_notification=True)


async def preprocess_text(text: str) -> str:
    permitted = ascii_letters + digits + cyrillic + punctuation
    processed_text = ''.join([ch for ch in text.strip() if ch in permitted])[:30]
    return processed_text


async def broadcast(text: str, comic_data: Union[Tuple, None] = None):
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
                    if comic_data:
                        await send_comic(user_id, comic_data=comic_data)
                    count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
    except Exception as err:
        logger.error(f"Couldn't broadcast on count {count}!", err)
    finally:
        await bot.send_message(ADMIN_ID, f"❗ <b>{count}/{len(subscribed_users)} messages were successfully sent.</b>")
        logger.info(f"{count}/{len(subscribed_users)} messages were successfully sent")
