from dataclasses import asdict, dataclass, field

from src.app.comics.image_utils.types import ImageTypeEnum
from src.core.types import LanguageEnum


def images_field_default_factory():
    return {
        ImageTypeEnum.DEFAULT: None,
        ImageTypeEnum.ENLARGED: None,
        ImageTypeEnum.THUMBNAIL: None,
    }


@dataclass(slots=True)
class TranslationCreateDTO:
    issue_number: int | None
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[ImageTypeEnum, str | None] = field(
        default_factory=images_field_default_factory,
    )
    language: LanguageEnum = LanguageEnum.EN
    is_draft: bool = False

    def to_dict(self):
        return asdict(self)
