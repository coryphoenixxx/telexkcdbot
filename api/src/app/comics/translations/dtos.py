from dataclasses import asdict, dataclass, field

from src.app.comics.image_utils.types import ImageTypeEnum
from src.core.types import LanguageEnum


@dataclass(slots=True)
class TranslationCreateDTO:
    issue_number: int | None
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[ImageTypeEnum, str | None] = field(
        default_factory=lambda: {k.value: None for k in ImageTypeEnum},
    )
    language: LanguageEnum = LanguageEnum.EN
    is_draft: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass(slots=True)
class TranslationGetDTO:
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[ImageTypeEnum, str | None]
    is_draft: bool = False
