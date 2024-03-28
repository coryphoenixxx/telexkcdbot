import logging

from fastapi import FastAPI
from faststream.nats.fastapi import NatsRouter

from api.presentation.web.controllers import comic_router, image_router, translation_router

root_router = NatsRouter(
    prefix="/api",
    log_level=logging.DEBUG,
)


@root_router.get("/healthcheck", status_code=200)
async def healthcheck():
    return {"message": "API is available."}


def register_routers(app: FastAPI) -> None:
    root_router.include_router(comic_router)
    root_router.include_router(translation_router)
    root_router.include_router(image_router)

    app.include_router(root_router)
