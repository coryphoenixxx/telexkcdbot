import aiofiles
import aiofiles.os
import aiohttp

from string import ascii_letters, digits
from typing import Tuple, Union

from aiogram.types import Message, InputFile, ChatActions
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked, \
    UserDeactivated, MessageToEditNotFound, ChatNotFound, MessageCantBeEdited

from src.bot.loader import *
from src.bot.config import ADMIN_ID
from src.bot.keyboards import kboard


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

    link = await get_link(comic_id, comic_lang, title)
    headline = f"<b>{comic_id}. \"{link}\"</b>   <i>({public_date})</i>"

    await bot.send_message(user_id, headline, disable_web_page_preview=True)

    if is_specific:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>It's a peculiar comic!\n"
                                    f"It's preferable to view it in your browser.</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)

    try:
        if img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, img_url, disable_notification=True)
        elif img_url.endswith('.fileid'):
            await bot.send_photo(user_id, photo=img_url[:-7], disable_notification=True)
        else:
            await bot.send_photo(user_id,
                                 photo=InputFile(image_path.joinpath('no_image.png')),
                                 disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest):
        try:
            local_img_filename = await get_local_img_filename(img_url)
            local_file = InputFile(local_img_filename)
            msg_info = await bot.send_photo(user_id, photo=local_file, disable_notification=True)

            await aiofiles.os.remove(local_img_filename)

            file_id = msg_info['photo'][0]['file_id'] + '.fileid'
            if comic_lang == 'ru':
                await comics_db.update_ru_img_url(comic_id=comic_id, new_ru_img_url=file_id)
            else:
                await comics_db.update_img_url(comic_id=comic_id, new_img_url=file_id)
        except Exception as err:
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


async def get_local_img_filename(img_url: str) -> str:
    img_url = img_url.split('/')[-1]
    filename = img_url[-30:]
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as response:
            if response.ok:
                async with aiofiles.open(filename, mode='wb') as f:
                    await f.write(await response.read())

    return filename


async def get_link(comic_id: int, comic_lang: str, title: str) -> str:
    link_template = "<a href='{url}'>{title}</a>"

    if comic_lang == 'ru':
        url = f'https://xkcd.su/{comic_id}'
    else:
        url = f'https://xkcd.com/{comic_id}' if comic_id != 880 \
            else 'https://xk3d.xkcd.com/880/'  # Original image is broken

    return link_template.format(url=url, title=title)


async def get_comics_list_text(comics_ids: list, titles: list, comic_lang: str) -> str:
    headers_list = [f"<b>{str(i[0]) + '.':7}</b>\"{await get_link(i[0], comic_lang, i[1])}\"" \
                    for i in zip(comics_ids, titles)]

    text = '\n'.join(headers_list)

    return text


async def send_comics_list_text_in_bunches(user_id: int, comics_ids: list, titles: list, comic_lang: str = 'en'):
    for i in range(0, len(comics_ids) + 1, 50):
        end = i + 50
        if end > len(comics_ids):
            end = len(comics_ids)

        text = await get_comics_list_text(comics_ids[i:end], titles[i:end], comic_lang)
        await bot.send_message(user_id, text, disable_web_page_preview=True)
        await asyncio.sleep(0.5)


async def is_cyrillic(text: str) -> bool:
    cyr_set = set(cyrillic + punctuation)
    set_text = set(text)
    return set_text.issubset(cyr_set)


async def preprocess_text(text: str) -> str:
    text = text.strip()
    permitted = ascii_letters + digits + cyrillic + punctuation
    text = ''.join([ch for ch in text if ch in permitted])
    return text[:30]


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
    subscribed_users_ids = await users_db.get_subscribed_users()

    try:
        for user_id in user_ids:
            try:
                await bot.send_chat_action(user_id, ChatActions.TYPING)
            except (BotBlocked, UserDeactivated, ChatNotFound):
                await users_db.delete_user(user_id)
            else:
                if not comic_data:
                    await bot.send_message(user_id, text=text)
                    count += 1
                else:
                    if user_id in subscribed_users_ids:
                        await bot.send_message(user_id, text=text)
                        await send_comic(user_id, comic_data=comic_data)
                        count += 1

                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
    except Exception as err:
        logger.error("Couldn't broadcast!", err)
    finally:
        await bot.send_message(ADMIN_ID, f"❗ <b>{count} messages were successfully sent.</b>")
