import asyncio
import aioschedule


from aiogram.utils.executor import start_webhook, start_polling
from aiogram import Dispatcher
from aiogram.types import InputFile

from loader import users_db, comics_db, bot
from keyboard_ import kb
from parser_ import parser
from config_ import *


async def scheduler():
    aioschedule.every(600).seconds.do(check_last_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp: Dispatcher):
    await bot.delete_webhook()
    await users_db.create()
    await users_db.new_user(ADMIN_ID)

    await asyncio.sleep(2)

    await check_last_comic()
    asyncio.create_task(scheduler())
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

    await bot.send_message(chat_id=ADMIN_ID, text="<b>I'm here, in Your Power, My Lord...</b>")


async def on_shutdown(dp: Dispatcher):
    await bot.send_message(chat_id=ADMIN_ID, text="<b>Something killed Your squire, My Lord...</b>")


async def check_last_comic():
    async def get_subscribed_users():
        for user_id in (await users_db.subscribed_users):
            yield user_id

    db_last_comic_id = await comics_db.get_last_comic_id()
    real_last_comic_id = parser.get_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            data = await parser.get_full_comic_data(id)
            comic_values = tuple(data.values())
            await comics_db.add_new_comic(comic_values)

        count = 0
        try:
            async for user_id in get_subscribed_users():
                await bot.send_message(user_id, "<b>And here\'s new comic!</b> 🔥")
                comic_data = await comics_db.get_comic_data_by_id(real_last_comic_id)
                await mod_answer(user_id, data=comic_data)
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            print(f"{count} messages successful sent.")  # TODO: add to log?


async def mod_answer(user_id: int, data: dict, keyboard=kb.navigation):
    (comic_id,
     title,
     img_url,
     comment,
     public_date,
     is_specific) = data.values()

    await users_db.update_cur_comic_id(user_id, comic_id)  # TODO: replace by this all cur_comic_id?
    link = f'https://xkcd.com/{comic_id}' if comic_id != 880 else 'https://xk3d.xkcd.com/880/'  # TODO: link or url?
    headline = f"<b>{comic_id}. \"<a href='{link}'>{title}</a>\"</b>   <i>({public_date})</i>"
    comment = comment.replace('<', '').replace('>', '')

    await bot.send_message(chat_id=user_id,
                           text=headline,
                           disable_web_page_preview=True)
    if is_specific:
        await bot.send_message(chat_id=user_id,
                               text=f"It's a peculiar comic! ^^ It's preferable to view it "
                                    f"in <a href='{link}'>your browser</a>.",
                               disable_web_page_preview=True,
                               disable_notification=True)
    if img_url.endswith(('.png', '.jpg', '.jpeg')):
        await bot.send_photo(chat_id=user_id,
                             photo=img_url,
                             disable_notification=True)
    elif img_url.endswith('.gif'):
        await bot.send_animation(chat_id=user_id,
                                 animation=img_url,
                                 disable_notification=True)
    else:
        await bot.send_photo(chat_id=user_id,
                             photo=InputFile('static/no_image.png'),
                             disable_notification=True)
    await bot.send_message(chat_id=user_id,
                           text=f"<i>{comment}</i>",
                           reply_markup=await keyboard(user_id, comic_id),
                           disable_web_page_preview=True,
                           disable_notification=True)


if __name__ == "__main__":
    from handlers import dp
    if HEROKU:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=PORT,
        )
    else:
        start_polling(dispatcher=dp,
                      skip_updates=True,
                      on_startup=on_startup,
                      on_shutdown=on_shutdown)
