import datetime as dt
from collections.abc import Mapping
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, HttpUrl, PositiveInt

from backend.application.common.pagination import TotalCount
from backend.application.utils import cast_or_none
from backend.core.value_objects import (
    Language,
    TempFileID,
)

if TYPE_CHECKING:
    from backend.application.comic.dtos import (
        ComicResponseDTO,
        TagResponseDTO,
        TranslationImageResponseDTO,
        TranslationResponseDTO,
    )


class OKResponseSchema(BaseModel):
    message: str


class TempImageSchema(BaseModel):
    temp_image_id: TempFileID


class PaginationSchema(BaseModel):
    total: TotalCount
    limit: PositiveInt | None
    offset: PositiveInt | None


class TagResponseSchema(BaseModel):
    id: PositiveInt
    name: str

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> Self:
        return cls(id=dto.id.value, name=dto.name.value)


class TagResponseWBlacklistStatusSchema(TagResponseSchema):
    is_blacklisted: bool

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> Self:
        return cls(
            id=dto.id.value,
            name=dto.name.value,
            is_blacklisted=dto.is_blacklisted,
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
    image: "TranslationImageResponseSchema | None"
    has_translations: list[Language]

    @classmethod
    def from_dto(cls, dto: "ComicResponseDTO") -> Self:
        return cls(
            id=dto.id.value,
            number=dto.number.value if dto.number else None,
            title=dto.title,
            publication_date=dto.publication_date,
            translation_id=dto.translation_id.value,
            tooltip=dto.tooltip,
            xkcd_url=cast_or_none(HttpUrl, dto.xkcd_url),
            explain_url=cast_or_none(HttpUrl, dto.explain_url),
            click_url=cast_or_none(HttpUrl, dto.click_url),
            is_interactive=dto.is_interactive,
            tags=[TagResponseSchema.from_dto(dto) for dto in dto.tags],
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            has_translations=dto.has_translations,
        )


class TranslationResponseBaseSchema(BaseModel):
    id: int
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_url: HttpUrl | None
    image: "TranslationImageResponseSchema | None"


class TranslationResponseSchema(TranslationResponseBaseSchema):
    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> Mapping[Language, Self]:
        return {
            dto.language: cls(
                id=dto.id.value,
                comic_id=dto.comic_id.value,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_url=cast_or_none(HttpUrl, dto.source_url),
                image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            ),
        }


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: dict[Language, "TranslationResponseSchema"]

    @staticmethod
    def _prepare_and_filter(
        translations: list["TranslationResponseDTO"],
        filter_languages: list[Language] | None = None,
    ) -> dict[Language, TranslationResponseSchema]:
        translation_map: dict[Language, TranslationResponseSchema] = {}
        for tr in translations:
            if not filter_languages or tr.language in filter_languages:
                translation_map.update(TranslationResponseSchema.from_dto(tr))

        return translation_map

    @classmethod
    def from_dto(
        cls,
        dto: "ComicResponseDTO",
        filter_languages: list[Language] | None = None,
    ) -> Self:
        return cls(
            id=dto.id.value,
            number=dto.number.value if dto.number else None,
            title=dto.title,
            publication_date=dto.publication_date,
            translation_id=dto.translation_id.value,
            tooltip=dto.tooltip,
            xkcd_url=cast_or_none(HttpUrl, dto.xkcd_url),
            explain_url=cast_or_none(HttpUrl, dto.explain_url),
            click_url=cast_or_none(HttpUrl, dto.click_url),
            is_interactive=dto.is_interactive,
            tags=[TagResponseSchema.from_dto(dto) for dto in dto.tags],
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            has_translations=dto.has_translations,
            translations=cls._prepare_and_filter(dto.translations, filter_languages),
        )


class ComicsWMetadata(BaseModel):
    meta: PaginationSchema
    data: list[ComicResponseSchema]


class TranslationImageResponseSchema(BaseModel):
    id: int
    translation_id: int | None
    original: str
    converted: str | None

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationImageResponseDTO",
    ) -> Self:
        return cls(
            id=dto.id.value,
            translation_id=dto.translation_id.value if dto.translation_id else None,
            original=str(dto.original),
            converted=str(dto.converted),
        )


class TranslationWLanguageResponseSchema(TranslationResponseBaseSchema):
    language: Language

    @classmethod
    def from_dto(cls, dto: "TranslationResponseDTO") -> Self:
        return cls(
            id=dto.id.value,
            comic_id=dto.comic_id.value,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=cast_or_none(HttpUrl, dto.source_url),
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
        )


class TranslationWDraftStatusSchema(TranslationWLanguageResponseSchema):
    is_draft: bool

    @classmethod
    def from_dto(cls, dto: "TranslationResponseDTO") -> Self:
        return cls(
            id=dto.id.value,
            comic_id=dto.comic_id.value,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=cast_or_none(HttpUrl, dto.source_url),
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            is_draft=dto.is_draft,
        )
