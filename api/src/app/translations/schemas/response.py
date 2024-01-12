from typing import Any

from src.app.images.types import TranslationImageVersion
from src.app.translations.schemas.request import TranslationRequestSchema
from src.app.translations.types import TranslationID


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    images: dict[TranslationImageVersion, dict[str, Any]]
