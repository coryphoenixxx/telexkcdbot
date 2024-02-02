import datetime as dt

from pydantic import BaseModel, Field, HttpUrl, PositiveInt, field_validator
from shared.utils import cast_or_none

from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import TranslationImageID
from api.core.types import Language


class ComicRequestSchema(BaseModel):
    number: PositiveInt | None = Field(examples=["1"])
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    is_interactive: bool = False
    tags: list[str] = Field(examples=[("Tag1", "Tag2")])

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
    title: str
    tooltip: str | None
    transcript: str | None
    images: list[TranslationImageID] = Field(examples=[(1, 2)])

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str] | None:
        if tags:
            for tag in tags:
                if not tag.strip() or len(tag) < 2:
                    raise ValueError(f"{tag} is invalid.")
        return list({tag.strip() for tag in tags})

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
                title=self.title,
                language=Language.EN,
                tooltip=self.tooltip,
                transcript=self.transcript,
                images=self.images,
                is_draft=False,
            ),
        )
