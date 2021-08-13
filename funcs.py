from string import ascii_letters, digits

from aiogram.types import Message, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked, \
    UserDeactivated, MessageToEditNotFound, ChatNotFound, MessageCantBeEdited

from loader import *
from config import ADMIN_ID
from keyboard import kboard


cyrillic = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


async def send_comic(user_id: int, data: tuple, keyboard=kboard.navigation, comic_lang: str = 'en'):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data

    await users_db.update_cur_comic_info(user_id, comic_id, comic_lang)

    link = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '')

    await bot.send_message(user_id, headline, disable_web_page_preview=True)

    if is_specific:
        await bot.send_message(user_id,
                               text=f"❗❗❗ It's a peculiar comic! It's preferable to view it "
                                    f"in <a href='{link}'>your browser</a>.",
                               disable_web_page_preview=True,
                               disable_notification=True)

    try:
        if img_url.endswith(('.png', '.jpg', '.jpeg')):
            await bot.send_photo(user_id, photo=img_url, disable_notification=True)
        elif img_url.endswith('.gif'):
            await bot.send_animation(user_id, img_url, disable_notification=True)
        else:
            await bot.send_photo(user_id, InputFile('static/no_image.png'), disable_notification=True)
    except (InvalidHTTPUrlContent, BadRequest) as err:
        await bot.send_message(user_id,
                               text=f"❗❗❗ Can't get image, try it in your browser!",
                               disable_web_page_preview=True,
                               disable_notification=True)
        logger.error(f"Cant't send {comic_id} to {user_id} comic!", err)

    await bot.send_message(user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id, comic_lang),
                           disable_web_page_preview=True,
                           disable_notification=True)


def is_cyrillic(text: str) -> bool:
    cyr_set = set(cyrillic)
    set_text = set(text)
    return set_text.issubset(cyr_set)


async def preprocess_text(text: str) -> str:
    text = text.strip()
    permitted = ascii_letters + digits + cyrillic + ' '
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


async def broadcast(user_ids: tuple, text: str, comic_data: tuple = None):
    count = 0
    try:
        for user_id in user_ids:
            try:
                await bot.send_message(user_id, text=text)
            except (BotBlocked, UserDeactivated, ChatNotFound):
                await users_db.delete_user(user_id)
                continue
            else:
                if comic_data:
                    await send_comic(user_id, data=comic_data)
                count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # 20 messages per second (Limit: 30 messages per second)
    except Exception as err:
        logger.error("Couldn't broadcast!", err)
    finally:
        await bot.send_message(ADMIN_ID, f"❗ <b>{count} messages were successfully sent.</b>")
