from fastapi import FastAPI

from api.presentation.web.controllers import (
    comic_router,
    default_router,
    image_router,
    translation_router,
    user_router,
)


def register_routers(app: FastAPI) -> None:
    app.include_router(default_router)
    app.include_router(comic_router)
    app.include_router(translation_router)
    app.include_router(image_router)
    app.include_router(user_router)
