import asyncio

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.http_client import HttpClient

from api.application.image_saver import ImageSaveHelper
from api.core.settings import load_settings
from api.infrastructure.database import (
    DatabaseHolder,
    create_db_engine,
    create_db_session_factory,
)
from api.presentation.dependency_stubs import (
    BrokerDepStub,
    DatabaseHolderDepStub,
    DbEngineDepStub,
    HttpClientDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
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

    root_router = register_routers(app)

    app.add_middleware(ExceptionHandlerMiddleware)

    engine = create_db_engine(settings.db)
    db_session_factory = create_db_session_factory(engine)
    http_client = HttpClient(throttler=asyncio.Semaphore(5))

    app.dependency_overrides.update(
        {
            DbEngineDepStub: lambda: engine,
            DatabaseHolderDepStub: lambda: DatabaseHolder(
                session_factory=db_session_factory,
            ),
            UploadImageReaderDepStub: lambda: UploadImageHandler(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
                http_client=http_client,
            ),
            ImageFileSaverDepStub: lambda: ImageSaveHelper(
                static_dir=settings.app.static_dir,
            ),
            HttpClientDepStub: lambda: http_client,
            BrokerDepStub: lambda: root_router.broker,
        },
    )

    return app


app = create_app()
