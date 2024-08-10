import datetime as dt
from collections.abc import Mapping
from typing import TYPE_CHECKING

from pydantic import BaseModel, HttpUrl

from api.application.dtos.common import Language, Limit, Offset, TotalCount
from api.core.value_objects import ComicID, IssueNumber, TagID, TranslationID

if TYPE_CHECKING:
    from api.application.dtos.responses import (
        ComicResponseDTO,
        TagResponseDTO,
        TranslationImageResponseDTO,
        TranslationResponseDTO,
    )


class OKResponseSchema(BaseModel):
    message: str


class PaginationSchema(BaseModel):
    total: TotalCount
    limit: Limit | None
    offset: Offset | None


class TagResponseSchema(BaseModel):
    id: TagID
    name: str

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> "TagResponseSchema":
        return TagResponseSchema(id=dto.id, name=dto.name)


class TagResponseWBlacklistStatusSchema(TagResponseSchema):
    is_blacklisted: bool

    @classmethod
    def from_dto(cls, dto: "TagResponseDTO") -> "TagResponseWBlacklistStatusSchema":
        return TagResponseWBlacklistStatusSchema(
            id=dto.id,
            name=dto.name,
            is_blacklisted=dto.is_blacklisted,
        )


class ComicResponseSchema(BaseModel):
    id: ComicID
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[TagResponseSchema]
    translation_id: TranslationID
    xkcd_url: HttpUrl
    tooltip: str
    image: "TranslationImageResponseSchema | None"
    has_translations: list[Language]

    @classmethod
    def from_dto(cls, dto: "ComicResponseDTO") -> "ComicResponseSchema":
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
            image=TranslationImageResponseSchema.from_dto(dto.image),
            has_translations=dto.has_translations,
        )


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: Mapping[Language, "TranslationResponseSchema"]

    @classmethod
    def from_dto(
        cls,
        dto: "ComicResponseDTO",
        filter_languages: list[Language] | None = None,
    ) -> "ComicWTranslationsResponseSchema":
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
            image=[TranslationImageResponseSchema.from_dto(img) for img in dto.image],
            has_translations=dto.has_translations,
            translations=_prepare_and_filter(dto.translations, filter_languages),
        )


class ComicsWMetadata(BaseModel):
    meta: PaginationSchema
    data: list[ComicResponseSchema]


class TranslationResponseSchema(BaseModel):
    id: TranslationID
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_url: HttpUrl | None
    images: list["TranslationImageResponseSchema"]

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> Mapping[Language, "TranslationResponseSchema"]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                images=[TranslationImageResponseSchema.from_dto(img) for img in dto.image],
            ),
        }


def _prepare_and_filter(
    translations: list["TranslationResponseDTO"],
    filter_languages: list[Language] | None = None,
) -> Mapping[Language, TranslationResponseSchema]:
    translation_map = {}
    for tr in translations:
        if not filter_languages or tr.language in filter_languages:
            translation_map.update(TranslationResponseSchema.from_dto(tr))

    return translation_map


class TranslationImageResponseSchema(BaseModel):
    id: int
    translation_id: int
    original: str
    converted: str | None
    thumbnail: str | None

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationImageResponseDTO | None",
    ) -> "TranslationImageResponseSchema | None":
        if dto:
            return TranslationImageResponseSchema(
                id=dto.id,
                translation_id=dto.translation_id,
                original=str(dto.original_rel_path),
                converted=str(dto.converted_rel_path),
                thumbnail=str(dto.thumbnail_rel_path),
            )
        return None


class TranslationWLanguageResponseSchema(TranslationResponseSchema):
    language: Language

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> "TranslationWLanguageResponseSchema":
        return TranslationWLanguageResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            images=[TranslationImageResponseSchema.from_dto(img) for img in dto.image],
        )


class TranslationWDraftStatusSchema(TranslationWLanguageResponseSchema):
    is_draft: bool

    @classmethod
    def from_dto(
        cls,
        dto: "TranslationResponseDTO",
    ) -> "TranslationWDraftStatusSchema":
        return TranslationWDraftStatusSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            images=[TranslationImageResponseSchema.from_dto(img) for img in dto.image],
            is_draft=dto.is_draft,
        )
