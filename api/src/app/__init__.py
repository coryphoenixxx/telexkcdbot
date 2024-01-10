from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.core.database import DatabaseHolder, create_engine, create_session_factory
from src.core.settings import get_settings

from .comics.images.utils import ImageFileSaver, UploadImageReader
from .dependency_stubs import (
    DatabaseHolderDep,
    DbEngineDep,
    ImageFileSaverDep,
    UploadImageReaderDep,
)
from .events import lifespan
from .middlewares import ExceptionHandlerMiddleware
from .router import register_routers


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

    engine = create_engine(settings.db)
    session_factory = create_session_factory(engine)

    app.dependency_overrides.update(
        {
            DbEngineDep: lambda: engine,
            DatabaseHolderDep: lambda: DatabaseHolder(session_factory=session_factory),
            UploadImageReaderDep: lambda: UploadImageReader(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
            ),
            ImageFileSaverDep: lambda: ImageFileSaver(static_dir=settings.app.static_dir),
        },
    )

    return app
