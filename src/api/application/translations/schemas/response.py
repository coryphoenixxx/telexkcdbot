from typing import Any

from api.application.comics.types import ComicID
from api.application.images.types import TranslationImageVersion
from api.application.translations.schemas.request import TranslationRequestSchema
from api.application.translations.types import TranslationID


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    comic_id: ComicID
    images: dict[TranslationImageVersion, dict[str, Any]]
