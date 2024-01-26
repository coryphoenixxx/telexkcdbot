from fastapi import APIRouter, FastAPI

from api.application.comics.endpoints import router as comics_router
from api.application.images.endpoints import router as image_router
from api.application.translations.endpoints import router as translation_router


def register_routers(app: FastAPI):
    router = APIRouter(prefix="/api")

    router.include_router(comics_router)
    router.include_router(image_router)
    router.include_router(translation_router)

    app.include_router(router)
