from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.config_loader import load_config
from shared.http_client import AsyncHttpClient
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.cors import CORSMiddleware

from api.application.image_saver import ImageSaveHelper
from api.config import AppConfig
from api.infrastructure.database import create_db_engine, create_db_session_factory
from api.infrastructure.database.holder import DatabaseHolder
from api.presentation.events import lifespan
from api.presentation.router import register_routers
from api.presentation.upload_reader import UploadImageHandler
from api.presentation.web.middlewares import ExceptionHandlerMiddleware


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

    engine = create_db_engine(config.db)
    db_session_factory = create_db_session_factory(engine)
    http_client = AsyncHttpClient()

    app.dependency_overrides.update(
        {
            AsyncEngine: lambda: engine,
            DatabaseHolder: lambda: DatabaseHolder(
                session_factory=db_session_factory,
            ),
            UploadImageHandler: lambda: UploadImageHandler(
                tmp_dir=config.api.tmp_dir,
                upload_max_size=config.api.upload_max_size,
                http_client=http_client,
            ),
            ImageSaveHelper: lambda: ImageSaveHelper(
                static_dir=config.api.static_dir,
            ),
            AsyncHttpClient: lambda: http_client,
        },
    )

    return app


app = create_app()
