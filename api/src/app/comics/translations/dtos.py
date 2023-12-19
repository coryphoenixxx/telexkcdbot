from dataclasses import dataclass, field

from src.app.comics.image_utils.types import ComicImageType
from src.core.types import LanguageCode


def images_field_default_factory():
    return {
        ComicImageType.DEFAULT: None,
        ComicImageType.ENLARGED: None,
        ComicImageType.THUMBNAIL: None,
    }


@dataclass(slots=True)
class TranslationCreateDTO:
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[ComicImageType, str | None] = field(default_factory=images_field_default_factory)
    language_code: LanguageCode = LanguageCode.EN
    is_draft: bool = False
