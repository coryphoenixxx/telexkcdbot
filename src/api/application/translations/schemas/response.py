from api.application.comics.types import ComicID
from api.application.images.schemas import TranslationImageResponseSchema
from api.application.translations.schemas.request import TranslationRequestSchema
from api.application.translations.types import TranslationID


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    comic_id: ComicID
    images: list[TranslationImageResponseSchema]
