from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_ioc
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.config_loader import load_config
from starlette.middleware.cors import CORSMiddleware

from api.config import AppConfig
from api.ioc import ConfigsProvider, DbProvider, GatewaysProvider, HelpersProvider, ServicesProvider
from api.presentation.router import register_routers
from api.presentation.web.middlewares import ExceptionHandlerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app(config: AppConfig | None = None) -> FastAPI:
    if config is None:
        config = load_config(AppConfig)

    app = FastAPI(
        lifespan=lifespan,
        debug=config.api.debug,
        docs_url=config.api.docs_url,
        redoc_url=config.api.redoc_url,
        openapi_url=config.api.openapi_url,
        default_response_class=ORJSONResponse,
    )
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)

    container = make_async_container(
        ConfigsProvider(),
        DbProvider(),
        HelpersProvider(),
        GatewaysProvider(),
        ServicesProvider(),
    )

    setup_ioc(container, app)

    return app


app = create_app()
