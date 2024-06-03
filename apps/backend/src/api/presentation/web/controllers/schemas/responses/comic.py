import datetime as dt
from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses import TranslationResponseDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.infrastructure.database.my_types import Limit, Offset
from api.my_types import ComicID, IssueNumber, Language, TotalCount, TranslationID
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
    publication_date: dt.date
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[str]
    translation_id: TranslationID  # For transcript getting
    xkcd_url: HttpUrl
    title: str
    tooltip: str
    images: list[TranslationImageProcessedResponseSchema]
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
    translations: Mapping[Language, TranslationResponseSchema]

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
    meta: Pagination
    data: list[ComicResponseSchema]


def _prepare_and_filter(
    translations: list[TranslationResponseDTO],
    filter_languages: list[Language] | None = None,
) -> Mapping[Language, TranslationResponseSchema]:
    translation_map = {}
    for tr in translations:
        if not filter_languages or tr.language in filter_languages:
            translation_map.update(TranslationResponseSchema.from_dto(tr))

    return translation_map
