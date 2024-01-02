import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

from src.app.comics.endpoints import router as comics_router
from src.app.comics.images.endpoints import router as image_router
from src.app.comics.images.utils.cleaner import cleaner
from src.app.comics.images.utils.upload_reader import UploadImageReader
from src.core.config import AppConfig, settings
from src.core.database import db


def init_router(app: FastAPI):
    router = APIRouter(prefix="/api")
    router.include_router(comics_router)
    router.include_router(image_router)
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    asyncio.create_task(cleaner())
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

    return app


app = create_app(config=settings.app)
