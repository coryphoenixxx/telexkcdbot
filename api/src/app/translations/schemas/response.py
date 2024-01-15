from typing import Any

from src.app.comics.types import ComicID
from src.app.images.types import TranslationImageVersion
from src.app.translations.schemas.request import TranslationRequestSchema
from src.app.translations.types import TranslationID


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    comic_id: ComicID
    images: dict[TranslationImageVersion, dict[str, Any]]
