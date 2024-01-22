import asyncio

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.app.images.utils import ImageFileSaver, UploadImageReader
from src.core.database import DatabaseHolder, create_db_engine, create_db_session_factory
from src.core.settings import get_settings

from .dependency_stubs import (
    DatabaseHolderDepStub,
    DbEngineDepStub,
    HttpClientDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from .events import lifespan
from .middlewares import ExceptionHandlerMiddleware
from .router import register_routers
from .temp_utils import HttpClient


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        lifespan=lifespan,
        debug=settings.app.fastapi.debug,
        docs_url=settings.app.fastapi.docs_url,
        redoc_url=settings.app.fastapi.redoc_url,
        openapi_url=settings.app.fastapi.openapi_url,
        default_response_class=ORJSONResponse,
    )

    register_routers(app)

    app.add_middleware(ExceptionHandlerMiddleware)

    engine = create_db_engine(settings.db)
    db_session_factory = create_db_session_factory(engine)

    app.dependency_overrides.update(
        {
            DbEngineDepStub: lambda: engine,
            DatabaseHolderDepStub: lambda: DatabaseHolder(session_factory=db_session_factory),
            UploadImageReaderDepStub: lambda: UploadImageReader(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
            ),
            ImageFileSaverDepStub: lambda: ImageFileSaver(static_dir=settings.app.static_dir),
            HttpClientDepStub: lambda: HttpClient(throttler=asyncio.Semaphore(10)),
        },
    )

    return app