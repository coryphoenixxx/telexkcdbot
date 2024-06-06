from .comic import router as comic_router
from .default import router as default_router
from .image import router as image_router
from .translation import router as translation_router
from .user import router as user_router

__all__ = [
    "default_router",
    "comic_router",
    "image_router",
    "translation_router",
    "user_router",
]
