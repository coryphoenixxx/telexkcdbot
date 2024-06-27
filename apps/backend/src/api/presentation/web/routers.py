from fastapi import FastAPI

from api.presentation.web.controllers.comic import router as comic_router
from api.presentation.web.controllers.default import router as default_router
from api.presentation.web.controllers.image import router as image_router
from api.presentation.web.controllers.tag import router as tag_router
from api.presentation.web.controllers.translation import router as translation_router
from api.presentation.web.controllers.user import router as user_router


def register_routers(app: FastAPI) -> None:
    app.include_router(default_router)
    app.include_router(comic_router)
    app.include_router(translation_router)
    app.include_router(image_router)
    app.include_router(user_router)
    app.include_router(tag_router)
