import datetime as dt
from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.common import Language, Limit, Offset, TotalCount
from api.application.dtos.responses import (
    ComicResponseDTO,
    ComicResponseWTranslationsDTO,
    TranslationImageProcessedResponseDTO,
    TranslationResponseDTO,
)
from api.core.entities import ComicID, IssueNumber, TranslationID


class OKResponseSchema(BaseModel):
    message: str


class PaginationSchema(BaseModel):
    total: TotalCount
    limit: Limit | None
    offset: Offset | None


class ComicResponseSchema(BaseModel):
    id: ComicID
    number: IssueNumber | None
    publication_date: dt.date
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[str]
    translation_id: TranslationID  # For transcript getting
    xkcd_url: HttpUrl
    title: str
    tooltip: str
    images: list["TranslationImageProcessedResponseSchema"]
    has_translations: list[Language]

    @classmethod
    def from_dto(cls, dto: ComicResponseDTO) -> "ComicResponseSchema":
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
            tags=dto.tags,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            has_translations=dto.has_translations,
        )


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: Mapping[Language, "TranslationResponseSchema"]

    @classmethod
    def from_dto(
        cls,
        dto: ComicResponseWTranslationsDTO,
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
            tags=dto.tags,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
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
    images: list["TranslationImageProcessedResponseSchema"]

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> Mapping[Language, "TranslationResponseSchema"]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                images=[
                    TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images
                ],
            ),
        }


def _prepare_and_filter(
    translations: list[TranslationResponseDTO],
    filter_languages: list[Language] | None = None,
) -> Mapping[Language, TranslationResponseSchema]:
    translation_map = {}
    for tr in translations:
        if not filter_languages or tr.language in filter_languages:
            translation_map.update(TranslationResponseSchema.from_dto(tr))

    return translation_map


class TranslationImageOrphanResponseSchema(BaseModel):
    id: int
    original: str


class TranslationImageProcessedResponseSchema(TranslationImageOrphanResponseSchema):
    translation_id: int
    converted: str | None
    thumbnail: str | None

    @classmethod
    def from_dto(
        cls,
        dto: TranslationImageProcessedResponseDTO,
    ) -> "TranslationImageProcessedResponseSchema":
        return TranslationImageProcessedResponseSchema(
            id=dto.id,
            translation_id=dto.translation_id,
            original=dto.original_rel_path,
            converted=dto.converted_rel_path,
            thumbnail=dto.thumbnail_rel_path,
        )


class TranslationWLanguageResponseSchema(TranslationResponseSchema):
    language: Language

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> "TranslationWLanguageResponseSchema":
        return TranslationWLanguageResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
        )


class TranslationWDraftStatusSchema(TranslationWLanguageResponseSchema):
    is_draft: bool

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> "TranslationWDraftStatusSchema":
        return TranslationWDraftStatusSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            is_draft=dto.is_draft,
        )
