from fastapi import FastAPI
from faststream.nats.fastapi import NatsRouter

from api.application.comics.endpoints import router as comics_router
from api.application.images.endpoints import router as image_router
from api.application.translations.endpoints import router as translation_router

root_router = NatsRouter(prefix="/api")


def register_routers(app: FastAPI) -> NatsRouter:
    root_router.include_router(comics_router)
    root_router.include_router(image_router)
    root_router.include_router(translation_router)

    app.include_router(root_router)

    return root_router
