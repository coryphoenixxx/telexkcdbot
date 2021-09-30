from string import ascii_letters, digits
from typing import Tuple, Union

from aiogram.types import Message, InputFile, ChatActions
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked, \
    UserDeactivated, MessageToEditNotFound, ChatNotFound, MessageCantBeEdited

from .loader import *
from .config import ADMIN_ID
from .keyboards import kboard


cyrillic = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
punctuation = ' -(),.:;!?#+'
suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


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

    await bot.send_message(user_id, headline, disable_web_page_preview=True)

    if is_specific:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>This comic is peculiar!\n"
                                    f"It's preferable to view it in your browser.</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)

    try:
        if 'http' not in img_url:
            local_img = InputFile(img_path.joinpath(img_url))
            await bot.send_photo(user_id, photo=local_img, disable_notification=True)
        elif img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, img_url, disable_notification=True)
        else:
            await bot.send_photo(user_id,
                                 photo=InputFile(img_path.joinpath('no_image.png')),
                                 disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest) as err:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>Can't get image, try it in your browser!</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)
        logger.error(f"Cant't send {comic_id} to {user_id} comic! {err}")

    await bot.send_message(user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id, comic_lang),
                           disable_web_page_preview=True,
                           disable_notification=True)


async def get_link(comic_id: int, title: str, img_url: str, comic_lang: str) -> str:
    if 'http' not in img_url:
        return title
    else:
        if comic_lang == 'ru':
            url = f'https://xkcd.su/{comic_id}'
        else:
            url = f'https://xkcd.com/{comic_id}' if comic_id != 880 \
                                                 else 'https://xk3d.xkcd.com/880/'  # Original image is broken
        return f"<a href='{url}'>{title}</a>"


async def get_headline_text(*args) -> str:
    return f"<b>{str(args[0]) + '.':7}</b>\"{await get_link(*args)}\""


async def send_comics_list_text_in_bunches(user_id: int, comics_info: list, comic_lang: str = 'en'):
    ids, titles, img_urls = comics_info
    for i in range(0, len(ids) + 1, 50):
        end = i + 50
        if end > len(ids):
            end = len(ids)

        zipped_info = zip(ids[i:end], titles[i:end], img_urls[i:end])
        headlines = [await get_headline_text(*z, comic_lang) for z in zipped_info]
        text = '\n'.join(headlines)
        await bot.send_message(user_id, text, disable_web_page_preview=True)
        await asyncio.sleep(0.5)


async def is_cyrillic(text: str) -> bool:
    return set(text).issubset(cyrillic + punctuation)


async def preprocess_text(text: str) -> str:
    permitted = ascii_letters + digits + cyrillic + punctuation
    processed_text = ''.join([ch for ch in text.strip() if ch in permitted])[:30]
    return processed_text


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


def admin(func):
    async def decorator(msg: Message, state: FSMContext):
        if msg.from_user.id != int(ADMIN_ID):
            await msg.answer('Nope!)))')
        else:
            await func(msg, state)
    return decorator


async def broadcast(user_ids: tuple, text: str, comic_data: Union[Tuple, None] = None):
    count = 0
    subscribed_users = await users_db.get_subscribed_users()

    try:
        for user_id in user_ids:
            try:
                await bot.send_chat_action(user_id, ChatActions.TYPING)
            except (BotBlocked, UserDeactivated, ChatNotFound):
                await users_db.delete_user(user_id)
            else:
                if user_id in subscribed_users:
                    count += 1
                    await bot.send_message(user_id, text=text)
                    if comic_data:
                        await send_comic(user_id, comic_data=comic_data)
                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
    except Exception as err:
        logger.error(f"Couldn't broadcast on count {count}!", err)
    finally:
        await bot.send_message(ADMIN_ID, f"❗ <b>{count}/{len(subscribed_users)} messages were successfully sent.</b>")
        logger.info(f"{count}/{len(subscribed_users)} messages were successfully sent")
