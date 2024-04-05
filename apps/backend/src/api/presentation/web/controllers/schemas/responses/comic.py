import datetime as dt
from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses import TranslationResponseDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.types import ComicID, IssueNumber, LanguageCode, TotalCount
from api.infrastructure.database.types import Limit, Offset
from api.presentation.web.controllers.schemas.responses import (
    TranslationImageProcessedResponseSchema,
    TranslationResponseSchema,
)


class Pagination(BaseModel):
    total: TotalCount
    limit: Limit | None
    offset: Offset | None


class ComicResponseSchema(BaseModel):
    id: ComicID
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    transcript_raw: str
    source_link: HttpUrl
    explain_url: HttpUrl | None
    link_on_click: HttpUrl | None
    is_interactive: bool
    images: list[TranslationImageProcessedResponseSchema]
    tags: list[str]
    translation_langs: list[LanguageCode]

    @classmethod
    def from_dto(cls, dto: ComicResponseDTO) -> "ComicResponseSchema":
        return ComicResponseSchema(
            id=dto.id,
            number=dto.number,
            title=dto.title,
            publication_date=dto.publication_date,
            tooltip=dto.tooltip,
            transcript_raw=dto.transcript_raw,
            source_link=dto.xkcd_url,
            explain_url=dto.explain_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=dto.tags,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            translation_langs=dto.translation_langs,
        )


def prepare_and_filter(
    translations: list[TranslationResponseDTO],
    filter_languages: list[LanguageCode] | None = None,
) -> Mapping[LanguageCode, TranslationResponseSchema]:
    translation_map = {}

    for tr in translations:
        lang = tr.language
        if not filter_languages or lang in filter_languages:
            translation_map.update(TranslationResponseSchema.from_dto(tr))

    return translation_map


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: Mapping[LanguageCode, TranslationResponseSchema]

    @classmethod
    def from_dto(
        cls,
        dto: ComicResponseWTranslationsDTO,
        filter_languages: list[LanguageCode] | None = None,
    ) -> "ComicWTranslationsResponseSchema":
        return ComicWTranslationsResponseSchema(
            id=dto.id,
            number=dto.number,
            title=dto.title,
            publication_date=dto.publication_date,
            tooltip=dto.tooltip,
            transcript_raw=dto.transcript_raw,
            source_link=dto.xkcd_url,
            explain_url=dto.explain_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=dto.tags,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            translation_langs=dto.translation_langs,
            translations=prepare_and_filter(dto.translations, filter_languages),
        )


class ComicsWithMetadata(BaseModel):
    meta: Pagination
    data: list[ComicResponseSchema | ComicWTranslationsResponseSchema]
