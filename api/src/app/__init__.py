import asyncio

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

from src.app.comics.endpoints import router as comics_router
from src.app.comics.image_utils.cleaner import cleaner
from src.app.comics.image_utils.upload_reader import UploadImageReader
from src.app.comics.services import ImageSaver
from src.core.config import AppConfig, settings
from src.core.database import db


def init_router(app: FastAPI):
    router = APIRouter(prefix="/api")
    router.include_router(comics_router)
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    task = asyncio.create_task(cleaner(temp_dir=Path(settings.app.temp_dir)))
    yield
    await db.disconnect()


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        debug=config.fastapi.debug,
        docs_url=config.fastapi.docs_url,
        redoc_url=config.fastapi.redoc_url,
        default_response_class=ORJSONResponse,
    )

    init_router(app)

    UploadImageReader.setup(upload_max_size=eval(config.upload_max_size), temp_dir=config.temp_dir)
    ImageSaver.setup(static_dir=config.static_dir)

    return app


app = create_app(config=settings.app)
