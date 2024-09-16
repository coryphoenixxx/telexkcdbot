# type: ignore

import asyncio
import logging
import sys
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dishka import AsyncContainer, make_async_container
from dishka.integrations.aiogram import setup_dishka

from backend.infrastructure.config_loader import load_config
from backend.main.ioc.providers import (
    BotConfigProvider,
    BrokerConfigProvider,
    ComicServicesProvider,
    DatabaseConfigProvider,
    FileManagersProvider,
    FilesystemConfigProvider,
    PublisherRouterProvider,
    RepositoriesProvider,
    TransactionManagerProvider,
    TranslationImageServiceProvider,
)
from backend.presentation.tg_bot.config import BotAppConfig, BotConfig, BotRunMode, WebhookConfig
from backend.presentation.tg_bot.controllers.comic import router as comic_router
from backend.presentation.tg_bot.controllers.start import router as start_router

logger = logging.getLogger(__name__)


async def on_startup() -> None:
    message = "Bot successfully started."
    logger.info(message)


async def on_shutdown(bot: Bot, container: AsyncContainer) -> None:
    message = "Bot is stopping..."
    logger.info(message)
    await bot.session.close()
    await container.close()


async def setup_webhook(bot: Bot, config: WebhookConfig) -> None:
    await bot.set_webhook(
        url=config.url + config.path,
        secret_token=config.secret_token,
        drop_pending_updates=False,
    )


def webhook_run(
    bot: Bot,
    dp: Dispatcher,
    app_config: BotAppConfig,
    webhook_config: WebhookConfig,
) -> None:
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


async def polling_run(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook()
    await dp.start_polling(bot)


def main() -> None:
    container = make_async_container(
        DatabaseConfigProvider(),
        BotConfigProvider(),
        BrokerConfigProvider(),
        FilesystemConfigProvider(),
        TransactionManagerProvider(),
        FileManagersProvider(),
        RepositoriesProvider(),
        PublisherRouterProvider(),
        ComicServicesProvider(),
        TranslationImageServiceProvider(),
    )

    config = load_config(BotConfig, scope="bot")

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(comic_router)
    dp.startup.register(partial(on_startup))
    dp.shutdown.register(partial(on_shutdown, container=container))

    setup_dishka(container=container, router=dp, auto_inject=True)

    match config.run_method:
        case BotRunMode.POLLING:
            asyncio.run(polling_run(bot, dp))
        case BotRunMode.WEBHOOK:
            webhook_run(bot, dp, config.app, config.webhook)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
