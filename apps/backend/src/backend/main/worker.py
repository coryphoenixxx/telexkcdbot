import asyncio

from dishka import make_async_container
from dishka.integrations.faststream import FastStreamProvider, setup_dishka
from faststream import FastStream
from faststream.nats import NatsBroker

from backend.infrastructure.broker.config import NatsConfig
from backend.infrastructure.broker.controllers import router
from backend.infrastructure.config_loader import load_config
from backend.main.ioc.providers import (
    AppConfigProvider,
    BrokerConfigProvider,
    DatabaseConfigProvider,
    FileManagersProvider,
    ImageServiceProvider,
    RepositoriesProvider,
    TransactionManagerProvider,
)


def register_routers(broker: NatsBroker) -> None:
    broker.include_router(router)


def create_app() -> FastStream:
    config = load_config(NatsConfig, scope="nats")
    broker = NatsBroker(config.url)

    register_routers(broker)

    app = FastStream(broker)

    container = make_async_container(
        AppConfigProvider(),
        DatabaseConfigProvider(),
        BrokerConfigProvider(),
        TransactionManagerProvider(),
        FileManagersProvider(),
        RepositoriesProvider(),
        ImageServiceProvider(),
        FastStreamProvider(),
    )

    setup_dishka(container, app, auto_inject=True)

    return app


if __name__ == "__main__":
    app = create_app()
    asyncio.run(app.run())
