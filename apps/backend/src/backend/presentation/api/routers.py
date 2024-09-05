from fastapi import FastAPI

from backend.presentation.api.controllers.comic import router as comic_router
from backend.presentation.api.controllers.default import router as default_router
from backend.presentation.api.controllers.tag import router as tag_router
from backend.presentation.api.controllers.translation import router as translation_router
from backend.presentation.api.controllers.upload_image import router as image_router


def register_routers(app: FastAPI) -> None:
    app.include_router(default_router)
    app.include_router(comic_router)
    app.include_router(translation_router)
    app.include_router(image_router)
    app.include_router(tag_router)
