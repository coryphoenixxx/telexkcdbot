from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_ioc
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.infrastructure.config_loader import load_config
from backend.infrastructure.database.main import check_db_connection
from backend.main.ioc.providers import (
    APIConfigProvider,
    AppConfigProvider,
    BrokerConfigProvider,
    ComicServicesProvider,
    DatabaseConfigProvider,
    FileManagersProvider,
    PublisherRouterProvider,
    RepositoriesProvider,
    TagServiceProvider,
    TransactionManagerProvider,
    TranslationImageServiceProvider,
    TranslationServicesProvider,
)
from backend.presentation.api.config import APIConfig
from backend.presentation.api.middlewares import register_middlewares
from backend.presentation.api.routers import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    engine = await app.state.dishka_container.get(AsyncEngine)
    await check_db_connection(engine)  # TODO: handle
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    container = make_async_container(
        AppConfigProvider(),
        DatabaseConfigProvider(),
        BrokerConfigProvider(),
        APIConfigProvider(),
        TransactionManagerProvider(),
        FileManagersProvider(),
        PublisherRouterProvider(),
        RepositoriesProvider(),
        ComicServicesProvider(),
        TranslationImageServiceProvider(),
        TranslationServicesProvider(),
        TagServiceProvider(),
    )

    app = FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        root_path="/api",
    )

    register_middlewares(app)
    register_routers(app)

    setup_ioc(container, app)

    return app


def main() -> None:
    config = load_config(APIConfig, scope="api")
    uvicorn.run(
        "backend.main.api:create_app",
        factory=True,
        host=config.host,
        port=config.port,
    )


if __name__ == "__main__":
    main()
