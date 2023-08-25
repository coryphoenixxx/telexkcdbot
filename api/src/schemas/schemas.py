from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel
from src import dtos


class OrderType(str, Enum):
    DESC = "desc"
    ESC = "esc"


# StrEnum
class LanguageCode(str, Enum):
    EN = "en"
    RU = "ru"

    @classmethod
    def as_str(cls):
        return ', '.join([lang.value for lang in cls])


class ComicIDMixin(BaseModel):
    comic_id: int


class ComicFavCountMixin(BaseModel):
    favorite_count: int


class ComicTranslation(BaseModel):
    title: str
    comment: str
    transcript: str


ComicTranslations = Mapping[LanguageCode, ComicTranslation]


class ComicBase(BaseModel):
    publication_date: str
    is_special: bool
    reddit_url: str
    translations: ComicTranslations


class ComicValidFields(ComicBase, ComicFavCountMixin, ComicIDMixin):
    ...


class RequestComicSchema(ComicIDMixin, ComicBase):
    ...

    def to_dto(self) -> dtos.ComicRequestDto:
        translations = {}

        for lang_code, _content in self.translations.items():
            translations[lang_code] = dtos.ComicTranslationDto(
                title=self.translations[lang_code].title,
                comment=self.translations[lang_code].comment,
                transcript=self.translations[lang_code].transcript,
                image_url=None,
            )

        return dtos.ComicRequestDto(
            comic_id=self.comic_id,
            publication_date=self.publication_date,
            is_special=self.is_special,
            reddit_url=self.reddit_url,
            translations=translations,
        )
