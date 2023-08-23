from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from src.utils.filters import filter_keys


class LanguageCode(str, Enum):
    EN = "en"
    RU = "ru"


@dataclass(slots=True)
class ComicTranslationContent:
    title: str
    image_url: str
    comment: str
    transcript: str


ComicTranslations = Mapping[LanguageCode, ComicTranslationContent]


@dataclass(slots=True)
class ComicResponse:
    comic_id: int
    publication_date: str
    is_special: bool
    reddit_url: str
    translations: ComicTranslations
    favorite_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def _filter_by_languages(self, comic_data: dict, language_list: Sequence[str]):
        translations: dict = comic_data['translations']
        for lang_code, _content in translations.copy().items():
            if lang_code not in language_list:
                del comic_data['translations'][lang_code]
        return comic_data

    def filter(self, languages: str | None, fields: str | None) -> dict[str, Any]:
        comic_data = self.to_dict()

        if languages:
            comic_data = self._filter_by_languages(comic_data, languages.split(','))

        if fields:
            comic_data = filter_keys(comic_data, fields.split(','))

        return comic_data


@dataclass(slots=True)
class ComicRequest:
    ...
