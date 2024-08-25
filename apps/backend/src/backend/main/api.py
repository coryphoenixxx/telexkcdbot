from collections.abc import Generator
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_ioc
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.infrastructure.database.main import check_db_connection
from backend.main.ioc.providers import (
    BrokerProvider,
    ComicServicesProvider,
    ConfigsProvider,
    DatabaseProvider,
    HelpersProvider,
    RepositoriesProvider,
    TagServiceProvider,
    TranslationImageServiceProvider,
)
from backend.presentation.api.middlewares import register_middlewares
from backend.presentation.api.routers import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, None, None]:
    engine = await app.state.dishka_container.get(AsyncEngine)
    await check_db_connection(engine)
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    container = make_async_container(
        ConfigsProvider(),
        DatabaseProvider(),
        HelpersProvider(),
        BrokerProvider(),
        RepositoriesProvider(),
        ComicServicesProvider(),
        TranslationImageServiceProvider(),
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


if __name__ == "__main__":
    uvicorn.run(
        "backend.main.api:create_app",
        factory=True,
        reload=True,
        reload_delay=3,
    )
