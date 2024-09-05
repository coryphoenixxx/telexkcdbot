import datetime as dt
from collections.abc import Mapping
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, HttpUrl, PositiveInt

from backend.core.value_objects import (
    Language,
    TempFileID,
)
from backend.infrastructure.database.dtos import Limit, Offset, TotalCount

if TYPE_CHECKING:
    from backend.application.dtos import (
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
    limit: Limit | None
    offset: Offset | None


class TagResponseSchema(BaseModel):
    id: PositiveInt
    name: str

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> Self:
        return TagResponseSchema(id=dto.id, name=dto.name)


class TagResponseWBlacklistStatusSchema(TagResponseSchema):
    is_blacklisted: bool

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> Self:
        return TagResponseWBlacklistStatusSchema(
            id=dto.id,
            name=dto.name,
            is_blacklisted=dto.is_blacklisted,
        )


class ComicResponseSchema(BaseModel):
    id: int
    number: int | None
    title: str
    publication_date: dt.date
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[TagResponseSchema]
    translation_id: int
    xkcd_url: HttpUrl
    tooltip: str
    image: "TranslationImageResponseSchema | None"
    has_translations: list[Language]

    @classmethod
    def from_dto(cls, dto: "ComicResponseDTO") -> Self:
        return ComicResponseSchema(
            id=dto.id,
            number=dto.number,
            title=dto.title,
            publication_date=dto.publication_date,
            translation_id=dto.translation_id,
            tooltip=dto.tooltip,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            click_url=dto.click_url,
            is_interactive=dto.is_interactive,
            tags=[TagResponseSchema.from_dto(dto) for dto in dto.tags],
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            has_translations=dto.has_translations,
        )


class TranslationResponseSchema(BaseModel):
    id: int
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_url: HttpUrl | None
    image: "TranslationImageResponseSchema"

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> Mapping[Language, Self]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            ),
        }


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: Mapping[Language, "TranslationResponseSchema"]

    @staticmethod
    def _prepare_and_filter(
        translations: list["TranslationResponseDTO"],
        filter_languages: list[Language] | None = None,
    ) -> Mapping[Language, TranslationResponseSchema]:
        translation_map = {}
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
        return ComicWTranslationsResponseSchema(
            id=dto.id,
            number=dto.number,
            title=dto.title,
            publication_date=dto.publication_date,
            translation_id=dto.translation_id,
            tooltip=dto.tooltip,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            click_url=dto.click_url,
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
    translation_id: int
    original: str
    converted: str | None

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationImageResponseDTO",
    ) -> Self:
        return TranslationImageResponseSchema(
            id=dto.id,
            translation_id=dto.translation_id,
            original=str(dto.original),
            converted=str(dto.converted),
        )


class TranslationWLanguageResponseSchema(TranslationResponseSchema):
    language: Language

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> Self:
        return TranslationWLanguageResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
        )


class TranslationWDraftStatusSchema(TranslationWLanguageResponseSchema):
    is_draft: bool

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> Self:
        return TranslationWDraftStatusSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            image=TranslationImageResponseSchema.from_dto(dto.image) if dto.image else None,
            is_draft=dto.is_draft,
        )
