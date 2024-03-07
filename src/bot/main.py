import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from shared.api_rest_client import APIRESTClient
from shared.http_client.async_http_client import AsyncHttpClient

from bot.config import AppConfig, load_settings

router = Router()

api_client = APIRESTClient(client=AsyncHttpClient())


@router.message()
async def echo_handler(message: types.Message) -> None:
    number = int(message.text)

    comic = await api_client.get_comic_by_number(number)

    print(comic)


async def on_startup(bot: Bot, config: AppConfig):
    await bot.set_webhook(
        f"{config.base_webhook_url}{config.webhook_path}",
        secret_token=config.webhook_secret,
        drop_pending_updates=False,
    )


def main():
    settings = load_settings()

    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )

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
