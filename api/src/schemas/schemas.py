from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel
from src import dtos


class OrderType(str, Enum):
    DESC = 'desc'
    ESC = 'esc'


# StrEnum
class LanguageCode(str, Enum):
    EN = 'en'
    RU = 'ru'

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


class ComicOriginRequestSchema(BaseModel):
    comic_id: int
    publication_date: str
    is_special: bool
    reddit_url: str
    title: str
    comment: str
    transcript: str
    image: str | None = None

    def to_dto(self, image_path: str | None = None):
        translation = dtos.ComicRequestTranslationDTO(
            comic_id=self.comic_id,
            language_code=LanguageCode('en'),
            title=self.title,
            comment=self.comment,
            transcript=self.transcript,
            image_url=image_path,
        )

        return dtos.ComicOriginRequestDTO(
            comic_id=self.comic_id,
            publication_date=self.publication_date,
            is_special=self.is_special,
            reddit_url=self.reddit_url,
            text_data=translation,
        )
