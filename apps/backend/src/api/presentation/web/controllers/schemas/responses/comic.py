import datetime as dt
from collections.abc import Mapping
from functools import reduce

from pydantic import BaseModel, HttpUrl
from shared.types import LanguageCode

from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.types import ComicID, IssueNumber, Limit, Offset, TotalCount
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
        )


class ComicWTranslationsResponseSchema(ComicResponseSchema):
    translations: Mapping[LanguageCode, TranslationResponseSchema]

    @classmethod
    def from_dto(
        cls,
        dto: ComicResponseWTranslationsDTO,
    ) -> "ComicWTranslationsResponseSchema":
        translation_map = (
            reduce(
                lambda d1, d2: d1 | d2,
                [TranslationResponseSchema.from_dto(t) for t in dto.translations],
            )
            if dto.translations
            else {}
        )

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
            translations=translation_map,
        )


class ComicsWithMetadata(BaseModel):
    meta: Pagination
    data: list[ComicResponseSchema | ComicWTranslationsResponseSchema]
