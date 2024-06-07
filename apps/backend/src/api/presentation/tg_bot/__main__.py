import asyncio
import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dishka import AsyncContainer, make_async_container
from dishka.integrations.aiogram import setup_dishka
from shared.config_loader import load_config

from api.infrastructure.di.providers import (
    ConfigsProvider,
    DbProvider,
    GatewaysProvider,
    HelpersProvider,
    ServicesProvider,
)
from api.presentation.tg_bot.config import AppConfig, BotConfig, BotRunMode, WebhookConfig
from api.presentation.tg_bot.handlers.comic import router as comic_router
from api.presentation.tg_bot.handlers.start import router as start_router

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, admin_id: int):
    message = "Bot successfully started."
    await bot.send_message(chat_id=admin_id, text=message)
    logger.info(message)


async def on_shutdown(bot: Bot, admin_id: int, ioc: AsyncContainer):
    message = "Bot is stopping..."
    logger.info(message)
    await bot.send_message(chat_id=admin_id, text=message)
    await bot.session.close()
    await ioc.close()


async def setup_webhook(bot: Bot, config: WebhookConfig):
    await bot.set_webhook(
        url=config.url + config.path,
        secret_token=config.secret_token,
        drop_pending_updates=False,
    )


def webhook_run(
        bot: Bot,
        dp: Dispatcher,
        app_config: AppConfig,
        webhook_config: WebhookConfig,
):
    dp.startup.register(partial(setup_webhook, config=webhook_config))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_config.secret_token,
    )

    webhook_requests_handler.register(app, path=webhook_config.path)

    setup_application(app, dp, bot=bot)

    web.run_app(
        app,
        host=app_config.host,
        port=app_config.port,
    )


async def polling_run(bot: Bot, dp: Dispatcher):
    await bot.delete_webhook()
    await dp.start_polling(bot)


def main():
    config = load_config(BotConfig, scope="bot")

    ioc = make_async_container(
        ConfigsProvider(),
        DbProvider(),
        HelpersProvider(),
        GatewaysProvider(),
        ServicesProvider(),
    )

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )  # TODO: get bot instance from ioc

    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(comic_router)
    dp.startup.register(partial(on_startup, admin_id=config.admin_id))
    dp.shutdown.register(partial(on_shutdown, admin_id=config.admin_id, ioc=ioc))

    setup_dishka(container=ioc, router=dp, auto_inject=True)

    match config.run_method:
        case BotRunMode.POLLING:
            asyncio.run(polling_run(bot, dp))
        case BotRunMode.WEBHOOK:
            webhook_run(bot, dp, config.app, config.webhook)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
