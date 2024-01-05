from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.core.database import DatabaseHolder, create_engine, create_session_factory
from src.core.settings import get_settings

from .cleaner import Cleaner
from .comics.images.utils import UploadImageReader
from .comics.images.utils.image_saver import ImageFileSaver
from .dependency_stubs import (
    CleanerStub,
    DatabaseHolderStub,
    DbEngineStub,
    ImageFileSaverStub,
    UploadImageReaderStub,
)
from .events import lifespan
from .exception_handlers import register_exceptions
from .router import register_routers


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        lifespan=lifespan,
        debug=settings.app.fastapi.debug,
        docs_url=settings.app.fastapi.docs_url,
        redoc_url=settings.app.fastapi.redoc_url,
        default_response_class=ORJSONResponse,
    )

    register_routers(app)
    register_exceptions(app)

    engine = create_engine(settings.db)
    session_factory = create_session_factory(engine)

    app.dependency_overrides.update(
        {
            DbEngineStub: lambda: engine,
            DatabaseHolderStub: lambda: DatabaseHolder(session_factory=session_factory),
            CleanerStub: lambda: Cleaner(tmp_dir=settings.app.tmp_dir),
            UploadImageReaderStub:
                lambda: UploadImageReader(
                    tmp_dir=settings.app.tmp_dir,
                    upload_max_size=eval(settings.app.upload_max_size),
                ),
            ImageFileSaverStub: lambda: ImageFileSaver(static_dir=settings.app.static_dir),
        },
    )

    return app
