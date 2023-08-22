import functools
from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel
from src import dtos


class OrderType(str, Enum):
    DESC = "desc"
    ESC = "esc"


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
    image_url: str
    comment: str
    transcript: str

    # def filter(self, ext_field_set: set[str]) -> dict:
    #     return self.model_dump(include=ext_field_set)


ComicTranslations = Mapping[LanguageCode, ComicTranslation]


class ComicBase(BaseModel):
    publication_date: str
    is_special: bool
    reddit_url: str
    translations: ComicTranslations


class ComicSchema(ComicBase, ComicFavCountMixin, ComicIDMixin):
    ...

    # def filter(self, language: LanguageCode | None, fields: str | None) -> dict:
    #     if fields:
    #         ext_field_set = {'comic_id', 'language_code'} | set(fields.split(','))
    #         filtered_dump = self.model_dump(include=ext_field_set)
    #         filtered_dump['translations'] = [tr.filter(ext_field_set) for tr in self.translations]
    #     else:
    #         filtered_dump = self.model_dump()
    #
    #     if language:
    #         filtered_dump['translations'] = [
    #             tr for tr in filtered_dump['translations'] if
    #             tr['language_code'] == language
    #         ]
    #
    #     return filtered_dump

    @classmethod
    @property
    @functools.cache
    def valid_field_names(cls) -> tuple[str]:
        field_set = ComicSchema.model_fields.keys() | ComicTranslation.model_fields.keys()
        field_set -= {'language_code', 'comic_id', 'translations'}
        return tuple(sorted(field_set))


class PostComic(ComicIDMixin, ComicBase):
    ...

    def to_dto(self) -> dtos.ComicResponse:
        return dtos.ComicResponse(
            comic_id=self.comic_id,
            publication_date=self.publication_date,
            is_special=self.is_special,
            reddit_url=self.reddit_url,
            translations={
                lang_code: dtos.ComicTranslationContent(
                    title=tr_content.title,
                    image_url=tr_content.image_url,
                    comment=tr_content.comment,
                    transcript=tr_content.transcript,
                )
                for lang_code, tr_content in self.translations.items()
            },
        )


class PutComic(ComicBase):
    ...
