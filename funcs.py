from string import ascii_letters, digits

from aiogram.types import Message, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified, BadRequest, InvalidHTTPUrlContent, BotBlocked, \
    UserDeactivated, MessageToEditNotFound, ChatNotFound, MessageCantBeEdited

from loader import *
from config import ADMIN_ID
from keyboard import kboard

cyrillic = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
punctuation = ' -(),.:;!?#+'
suppress_exceptions = (AttributeError, MessageNotModified, MessageToEditNotFound, MessageCantBeEdited)


async def get_link(comic_id, comic_lang, title):
    link = "<a href='{url}'>{title}</a>"
    if comic_lang == 'ru':
        url = f'https://xkcd.ru/{comic_id}'
    else:
        url = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'

    return link.format(url=url, title=title)


async def get_comics_list_text(comics_ids, titles, comic_lang):
    headers_list = [f"<b>{str(i[0]) + '.':7}</b>\"{await get_link(i[0], comic_lang, i[1])}\"" \
                    for i in zip(comics_ids, titles)]
    if len(headers_list) > 50:
        headers_list = headers_list[:50]
        headers_list.append('...')

    text = '\n'.join(headers_list)

    return text


async def is_cyrillic(text: str) -> bool:
    cyr_set = set(cyrillic + punctuation)
    set_text = set(text)
    return set_text.issubset(cyr_set)


async def preprocess_text(text: str) -> str:
    text = text.strip()
    permitted = ascii_letters + digits + cyrillic + punctuation
    text = ''.join([ch for ch in text if ch in permitted])
    return text[:30]


async def send_comic(user_id: int, data: tuple, keyboard=kboard.navigation, comic_lang: str = 'en'):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data

    await users_db.update_cur_comic_info(user_id, comic_id, comic_lang)

    link = await get_link(comic_id, comic_lang, title)
    headline = f"<b>{comic_id}. \"{link}\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '').strip()

    await bot.send_message(user_id, headline, disable_web_page_preview=True)

    if is_specific:
        await bot.send_message(user_id,
                               text=f"❗❗❗ <b>It's a peculiar comic!\nIt's preferable to view it "
                                    f"in your browser.</b>",
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
                               text=f"❗❗❗ <b>Can't get image, try it in your browser!</b>",
                               disable_web_page_preview=True,
                               disable_notification=True)
        logger.error(f"Cant't send {comic_id} to {user_id} comic!", err)

    await bot.send_message(user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id, comic_lang),
                           disable_web_page_preview=True,
                           disable_notification=True)


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


async def fill_comic_db():
    from tqdm import trange

    async def parse(comic_id):
        async with sem:
            data = await parser.get_full_comic_data(comic_id)
        comics_data.append(data)

    async def write_to_db():
        comics_data.sort(key=lambda x: x[0])
        while comics_data:
            await comics_db.add_new_comic(comics_data.pop(0))

    async def gather(start, end):
        tasks = []
        for comic_id in range(start, end):
            if comic_id not in all_comics_ids:
                task = asyncio.create_task(parse(comic_id))
                tasks.append(task)

        await asyncio.gather(*tasks)

    async def main():
        logger.info("Start filling the comics db.")
        latest = (await parser.xkcd_latest_comic_id)
        chunk = 20
        for i in trange(1, latest + 1, chunk):
            end = i + chunk
            if end > latest:
                end = latest + 1
            await gather(i, end)
            await write_to_db()
        logger.info("Finish filling the comics db.")

    comics_data = []
    sem = asyncio.Semaphore(64)  # limits simultaneous connections on windows

    await comics_db.create()
    all_comics_ids = await comics_db.all_comics_ids

    await main()
