import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

from api.app.comics.endpoints import router as comics_router
from api.app.comics.image_utils.reader import ImageReader
from api.app.comics.services import ImageSaver
from api.core.config import AppConfig, settings
from api.core.database import db


def init_router(app: FastAPI):
    router = APIRouter(prefix="/api")
    router.include_router(comics_router)
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await ImageReader.start_cleaner()
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
    os.makedirs(config.static_dir, exist_ok=True)

    ImageReader.setup(upload_max_size=eval(config.upload_max_size), temp_dir=config.temp_dir)
    ImageSaver.setup(static_dir=config.static_dir)

    return app


app = create_app(config=settings.app)
