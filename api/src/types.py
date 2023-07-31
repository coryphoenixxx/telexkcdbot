import functools
from enum import Enum

from pydantic import BaseModel


class OrderType(str, Enum):
    DESC = "desc"
    ESC = "esc"


class LanguageCode(str, Enum):
    EN = "en"
    RU = "ru"


class ComicIDMixin(BaseModel):
    comic_id: int


class ComicFavCountMixin(BaseModel):
    favorite_count: int


class ComicTranslation(BaseModel):
    language_code: LanguageCode
    title: str
    image_url: str
    comment: str
    transcript: str

    def filter(self, ext_field_set: set[str]) -> dict:
        return self.model_dump(include=ext_field_set)


class ComicBase(BaseModel):
    publication_date: str
    is_specific: bool
    translations: list[ComicTranslation]


class ComicDTO(ComicBase, ComicFavCountMixin, ComicIDMixin):
    def filter(self, language: LanguageCode | None, fields: str | None) -> dict:
        if fields:
            ext_field_set = {'comic_id', 'language_code'} | set(fields.split(','))
            filtered_dump = self.model_dump(include=ext_field_set)
            filtered_dump['translations'] = [tr.filter(ext_field_set) for tr in self.translations]
        else:
            filtered_dump = self.model_dump()

        if language:
            filtered_dump['translations'] = [
                tr for tr in filtered_dump['translations'] if
                tr['language_code'] == language
            ]

        return filtered_dump

    @classmethod
    @property
    @functools.cache
    def valid_field_names(cls) -> tuple[str]:
        field_set = ComicDTO.model_fields.keys() | ComicTranslation.model_fields.keys()
        field_set -= {'language_code', 'comic_id', 'translations'}
        return tuple(sorted(field_set))


class PostComic(ComicIDMixin, ComicBase):
    ...


class PutComic(ComicBase):
    ...
