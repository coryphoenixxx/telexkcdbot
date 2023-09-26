from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from src.helpers.filters import filter_keys


class LanguageCode(str, Enum):
    EN = "en"
    RU = "ru"


@dataclass(slots=True)
class ComicTranslationDto:
    title: str
    comment: str
    transcript: str
    image_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ComicTranslations = Mapping[LanguageCode, ComicTranslationDto]


@dataclass(slots=True)
class ComicResponseDto:
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


# @dataclass(slots=True)
# class ComicRequestDto:
#     comic_id: int
#     publication_date: str
#     is_special: bool
#     reddit_url: str
#     translations: ComicTranslations
#
#     def to_dict(self, exclude=Sequence[str]) -> dict[str, Any]:
#         d = asdict(self)
#         for field in exclude:
#             d.pop(field)
#         return d


@dataclass(slots=True)
class ImageObjDto:
    comic_lang: str
    comic_id: int
    path: str
    extension: str



@dataclass(slots=True)
class ComicRequestTranslationDTO:
    comic_id: int
    language_code: LanguageCode
    title: str
    comment: str
    transcript: str
    image_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ComicOriginRequestDTO:
    comic_id: int
    publication_date: str
    is_special: bool
    reddit_url: str
    text_data: ComicRequestTranslationDTO

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop('text_data')
        return d
