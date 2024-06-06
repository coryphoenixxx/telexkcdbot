from dishka import make_async_container
from dishka.integrations.faststream import (
    FastStreamProvider,
)
from dishka.integrations.faststream import setup_dishka as setup_ioc
from faststream import FastStream
from faststream.nats import NatsBroker

from api.infrastructure.di.providers import (
    ConfigsProvider,
    DbProvider,
    GatewaysProvider,
    HelpersProvider,
    ServicesProvider,
)
from api.presentation.events.contollers import router


def register_routers(broker: NatsBroker):
    broker.include_router(router)


def create_app() -> FastStream:
    broker = NatsBroker()

    register_routers(broker)

    app = FastStream(broker)

    setup_ioc(
        make_async_container(
            ConfigsProvider(),
            DbProvider(),
            HelpersProvider(),
            GatewaysProvider(),
            ServicesProvider(),
            FastStreamProvider(),
        ),
        app,
        auto_inject=True,
    )

    return app
