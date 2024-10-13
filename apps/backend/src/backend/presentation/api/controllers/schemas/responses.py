import datetime as dt
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, HttpUrl

from backend.domain.entities import TranslationStatus
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import Language

if TYPE_CHECKING:
    from backend.application.comic.responses import (
        ComicCompactResponseData,
        ComicResponseData,
        TagResponseData,
        TranslationImageResponseData,
        TranslationResponseData,
    )


class OKResponseSchema(BaseModel):
    message: str


class TempImageSchema(BaseModel):
    image_id: int


class PaginationSchema(BaseModel):
    total: int
    limit: int | None
    offset: int | None


class TagResponseSchema(BaseModel):
    id: int
    name: str
    is_visible: bool
    from_explainxkcd: bool

    @classmethod
    def from_data(cls, data: "TagResponseData") -> Self:
        return cls(
            id=data.id,
            name=data.name,
            is_visible=data.is_visible,
            from_explainxkcd=data.from_explainxkcd,
        )


class TranslationImageResponseSchema(BaseModel):
    id: int
    translation_id: int
    original: str | None
    converted: str | None
    x2: str | None
    pos: int

    @classmethod
    def from_data(
        cls,
        data: "TranslationImageResponseData",
    ) -> Self:
        return cls(
            id=data.id,
            translation_id=data.translation_id,
            original=data.original,
            converted=data.converted,
            x2=data.x2,
            pos=data.position_number,
        )


class ComicResponseSchema(BaseModel):
    id: int
    number: int | None
    title: str
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[TagResponseSchema]
    translation_id: int
    tooltip: str
    images: list[TranslationImageResponseSchema]
    has_translations: list[Language]

    @classmethod
    def from_data(cls, data: "ComicResponseData") -> Self:
        return cls(
            id=data.id,
            number=data.number,
            title=data.title,
            publication_date=data.publication_date,
            translation_id=data.translation_id,
            tooltip=data.tooltip,
            xkcd_url=cast_or_none(HttpUrl, data.xkcd_url),
            explain_url=cast_or_none(HttpUrl, data.explain_url),
            click_url=cast_or_none(HttpUrl, data.click_url),
            is_interactive=data.is_interactive,
            tags=[TagResponseSchema.from_data(data) for data in data.tags],
            images=[TranslationImageResponseSchema.from_data(image) for image in data.images],
            has_translations=data.has_translations,
        )


class ComicCompactResponseSchema(BaseModel):
    id: int
    number: int | None
    title: str
    publication_date: dt.date
    image_url: str | None

    @classmethod
    def from_data(cls, data: "ComicCompactResponseData") -> Self:
        return cls(
            id=data.id,
            number=data.number if data.number else None,
            title=data.title,
            publication_date=data.publication_date,
            image_url=data.image_url,
        )


class TranslationResponseSchema(BaseModel):
    id: int
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_url: HttpUrl | None
    images: list[TranslationImageResponseSchema]
    language: Language
    status: TranslationStatus

    @classmethod
    def from_data(
        cls,
        data: "TranslationResponseData",
    ) -> Self:
        return cls(
            id=data.id,
            comic_id=data.comic_id,
            language=data.language,
            title=data.title,
            tooltip=data.tooltip,
            translator_comment=data.translator_comment,
            source_url=cast_or_none(HttpUrl, data.source_url),
            status=data.status,
            images=[TranslationImageResponseSchema.from_data(image) for image in data.images],
        )


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: list[TranslationResponseSchema]

    @classmethod
    def from_data(cls, data: "ComicResponseData") -> Self:
        return cls(
            id=data.id,
            number=data.number if data.number else None,
            title=data.title,
            publication_date=data.publication_date,
            translation_id=data.translation_id,
            tooltip=data.tooltip,
            xkcd_url=cast_or_none(HttpUrl, data.xkcd_url),
            explain_url=cast_or_none(HttpUrl, data.explain_url),
            click_url=cast_or_none(HttpUrl, data.click_url),
            is_interactive=data.is_interactive,
            tags=[TagResponseSchema.from_data(data) for data in data.tags],
            images=[TranslationImageResponseSchema.from_data(image) for image in data.images],
            has_translations=data.has_translations,
            translations=[TranslationResponseSchema.from_data(tr) for tr in data.translations],
        )


class ComicsWPaginationSchema(BaseModel):
    meta: PaginationSchema
    data: list[ComicCompactResponseSchema]
