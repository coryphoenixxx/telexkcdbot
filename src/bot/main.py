import logging
import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import load_settings, AppConfig

router = Router()


@router.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def on_startup(bot: Bot, config: AppConfig):
    await bot.set_webhook(
        f"{config.base_webhook_url}{config.webhook_path}",
        secret_token=config.webhook_secret,
        drop_pending_updates=True,
    )


def main():
    settings = load_settings()

    bot = Bot(token=settings.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.include_router(router)

    dp.startup.register(partial(on_startup, config=settings.app))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.app.webhook_secret,
    )

    webhook_requests_handler.register(app, path=settings.app.webhook_path)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=settings.app.host, port=settings.app.port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
