import datetime as dt

from pydantic import BaseModel, HttpUrl, PositiveInt, field_validator
from shared.types import (
    LanguageCode,
)
from shared.utils import cast_or_none

from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import TranslationImageID


class ComicRequestSchema(BaseModel):
    number: PositiveInt | None
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        result = []
        for tag in tags:
            stripped_tag = tag.strip()
            if len(stripped_tag) < 2:
                raise ValueError(f"`{tag}` is invalid tag. Min length is 2.")
            else:
                result.append(stripped_tag)
        return result

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            number=self.number,
            publication_date=self.publication_date,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            link_on_click=cast_or_none(str, self.link_on_click),
            is_interactive=self.is_interactive,
            tags=self.tags,
        )


class ComicWithEnTranslationRequestSchema(ComicRequestSchema):
    en_title: str
    en_tooltip: str
    en_transcript_raw: str
    images: list[int]

    def to_dtos(self) -> tuple[ComicRequestDTO, TranslationRequestDTO]:
        return (
            ComicRequestDTO(
                number=self.number,
                publication_date=self.publication_date,
                xkcd_url=cast_or_none(str, self.xkcd_url),
                explain_url=cast_or_none(str, self.explain_url),
                link_on_click=cast_or_none(str, self.link_on_click),
                is_interactive=self.is_interactive,
                tags=self.tags,
            ),
            TranslationRequestDTO(
                comic_id=None,
                title=self.en_title,
                language=LanguageCode.EN,
                tooltip=self.en_tooltip,
                transcript_raw=self.en_transcript_raw,
                translator_comment="",
                images=[TranslationImageID(image_id) for image_id in self.images],
                source_link=cast_or_none(str, self.xkcd_url),
                is_draft=False,
            ),
        )
