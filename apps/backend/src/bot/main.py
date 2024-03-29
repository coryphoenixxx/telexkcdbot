import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import AppConfig, Config
from shared.api_rest_client import APIRESTClient
from shared.config_loader import load_config
from shared.http_client.async_http_client import AsyncHttpClient

router = Router()

api_client = APIRESTClient(http_client=AsyncHttpClient())


@router.message()
async def echo_handler(message: types.Message) -> None:
    number = int(message.text)

    comic = await api_client.get_comic_by_number(number)

    print(comic)


async def on_startup(bot: Bot, config: AppConfig):
    await bot.set_webhook(
        f"{config.webhook_url}{config.webhook_path}",
        secret_token=config.webhook_secret,
        drop_pending_updates=False,
    )


def main():
    config = load_config(Config)

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher()
    dp.include_router(router)
    dp.startup.register(partial(on_startup, config=config.app))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.app.webhook_secret,
    )

    webhook_requests_handler.register(app, path=config.app.webhook_path)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=config.app.host, port=config.app.port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
