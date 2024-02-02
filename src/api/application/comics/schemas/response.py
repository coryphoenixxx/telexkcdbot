import datetime as dt

from pydantic import BaseModel, Field, HttpUrl

from api.application.comics.dtos.response import ComicResponseWithTranslationsDTO, ComicResponseDTO
from api.application.comics.types import IssueNumber
from api.application.translations.schemas.response import TranslationResponseSchema


class ComicResponseSchema(BaseModel):
    id: int
    number: IssueNumber | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]

    @classmethod
    def from_dto(cls, dto: ComicResponseDTO) -> "ComicResponseSchema":
        return ComicResponseSchema(
            id=dto.id,
            number=dto.number,
            publication_date=dto.publication_date,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=dto.tags,
        )


class ComicWithTranslationsResponseSchema(ComicResponseSchema):
    translations: list[TranslationResponseSchema]

    @classmethod
    def from_dto(
        cls,
        dto: ComicResponseWithTranslationsDTO,
    ) -> "ComicWithTranslationsResponseSchema":
        return ComicWithTranslationsResponseSchema(
            id=dto.id,
            number=dto.number,
            publication_date=dto.publication_date,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=dto.tags,
            translations=[TranslationResponseSchema.from_dto(t) for t in dto.translations],
        )
