import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from shared.api_rest_client import APIRESTClient
from shared.config_loader import load_config

from bot.config import AppConfig, Config
from bot.handlers.main import router


async def on_startup(bot: Bot, config: AppConfig) -> None:
    await bot.set_webhook(
        f"{config.webhook_url}{config.webhook_path}",
        secret_token=config.webhook_secret,
        drop_pending_updates=False,
    )


async def on_shutdown(api_client: APIRESTClient) -> None:
    await api_client.stop()


def main():
    config = load_config(Config)

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    api_client = APIRESTClient(base_url=config.bot.api_url)

    dp = Dispatcher()
    dp.include_router(router)
    dp.startup.register(partial(on_startup, config=config.app))
    dp.shutdown.register(partial(on_shutdown, api_client=api_client))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.app.webhook_secret,
        api_client=api_client,
        img_prefix=config.app.webhook_url + '/static/',
    )

    webhook_requests_handler.register(app, path=config.app.webhook_path)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=config.app.host, port=config.app.port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
