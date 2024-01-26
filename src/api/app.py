import asyncio

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.http_client import HttpClient

from api.application.dependency_stubs import (
    DatabaseHolderDepStub,
    DbEngineDepStub,
    HttpClientDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from api.application.events import lifespan
from api.application.images.utils import ImageFileSaver, UploadImageReader
from api.application.middlewares import ExceptionHandlerMiddleware
from api.application.router import register_routers
from api.core.database import (
    DatabaseHolder,
    create_db_engine,
    create_db_session_factory,
)
from api.core.settings import load_settings


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

    register_routers(app)

    app.add_middleware(ExceptionHandlerMiddleware)

    engine = create_db_engine(settings.db)
    db_session_factory = create_db_session_factory(engine)

    app.dependency_overrides.update(
        {
            DbEngineDepStub: lambda: engine,
            DatabaseHolderDepStub: lambda: DatabaseHolder(
                session_factory=db_session_factory,
            ),
            UploadImageReaderDepStub: lambda: UploadImageReader(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
            ),
            ImageFileSaverDepStub: lambda: ImageFileSaver(
                static_dir=settings.app.static_dir,
            ),
            HttpClientDepStub: lambda: HttpClient(throttler=asyncio.Semaphore(5)),
        },
    )

    return app


app = create_app()
