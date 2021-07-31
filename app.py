import asyncio
import aioschedule

from aiogram.utils.executor import start_webhook, start_polling
from aiogram import Dispatcher

from loader import users_db, bot
from config_ import *
from handlers import check_last_comic


async def scheduler():
    delay = 60 * 10
    aioschedule.every(delay).seconds.do(check_last_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def on_startup(dp: Dispatcher):
    await bot.delete_webhook()
    await users_db.create()
    await users_db.new_user(ADMIN_ID)
    await check_last_comic()
    asyncio.create_task(scheduler())
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await bot.send_message(chat_id=ADMIN_ID, text="<b>I'm here, in Your Power, My Lord...</b>")


async def on_shutdown(dp: Dispatcher):
    await bot.send_message(chat_id=ADMIN_ID, text="<b>Something killed Your squire, My Lord...</b>")


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
