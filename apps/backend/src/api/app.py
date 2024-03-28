from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.http_client import AsyncHttpClient
from sqlalchemy.ext.asyncio import AsyncEngine

from api.application.image_saver import ImageSaveHelper
from api.infrastructure.database import (
    create_db_engine,
    create_db_session_factory,
)
from api.infrastructure.database.holder import DatabaseHolder
from api.infrastructure.settings import load_settings
from api.presentation.events import lifespan
from api.presentation.router import register_routers
from api.presentation.upload_reader import UploadImageHandler
from api.presentation.web.middlewares import ExceptionHandlerMiddleware


def create_app() -> FastAPI:
    settings = load_settings()

    app = FastAPI(
        lifespan=lifespan,
        debug=settings.app.debug,
        docs_url=settings.app.docs_url,
        redoc_url=settings.app.redoc_url,
        openapi_url=settings.app.openapi_url,
        default_response_class=ORJSONResponse,
    )
    app.add_middleware(ExceptionHandlerMiddleware)

    register_routers(app)

    engine = create_db_engine(settings.db)
    db_session_factory = create_db_session_factory(engine)
    http_client = AsyncHttpClient()

    app.dependency_overrides.update(
        {
            AsyncEngine: lambda: engine,
            DatabaseHolder: lambda: DatabaseHolder(
                session_factory=db_session_factory,
            ),
            UploadImageHandler: lambda: UploadImageHandler(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
                http_client=http_client,
            ),
            ImageSaveHelper: lambda: ImageSaveHelper(
                static_dir=settings.app.static_dir,
            ),
            AsyncHttpClient: lambda: http_client,
        },
    )

    return app


app = create_app()
