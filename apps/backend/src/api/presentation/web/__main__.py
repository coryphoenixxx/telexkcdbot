from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_ioc
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.infrastructure.di.providers import (
    BrokerProvider,
    ConfigsProvider,
    DbProvider,
    GatewaysProvider,
    HelpersProvider,
    ServicesProvider,
)
from api.presentation.web.middlewares import register_middlewares
from api.presentation.web.routers import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    container = make_async_container(
        ConfigsProvider(),
        DbProvider(),
        HelpersProvider(),
        GatewaysProvider(),
        ServicesProvider(),
        BrokerProvider(),
    )

    app = FastAPI(
        lifespan=lifespan,
        # debug=config.debug,
        # docs_url=config.docs_url,
        # redoc_url=config.redoc_url,
        # openapi_url=config.openapi_url,
        default_response_class=ORJSONResponse,
        root_path="/api",
    )

     # TODO: get app from ioc?

    register_middlewares(app)
    register_routers(app)

    setup_ioc(container, app)

    return app


if __name__ == "__main__":
    uvicorn.run(
        "api.presentation.web.__main__:create_app",
        factory=True,
        reload=True,
        reload_delay=1,
    )
