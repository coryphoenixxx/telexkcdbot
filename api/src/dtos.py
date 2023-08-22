from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum


class LanguageCode(str, Enum):
    EN = "en"
    RU = "ru"


@dataclass(slots=True)
class ComicTranslationContent:
    title: str
    image_url: str
    comment: str
    transcript: str

    def to_dict(self):
        return asdict(self)


ComicTranslations = Mapping[LanguageCode, ComicTranslationContent]


@dataclass(slots=True)
class ComicResponse:
    comic_id: int
    publication_date: str
    is_special: bool
    reddit_url: str
    translations: ComicTranslations
    favorite_count: int | None

    def to_dict(self):
        return asdict(self)


@dataclass(slots=True)
class ComicRequest:
    ...
