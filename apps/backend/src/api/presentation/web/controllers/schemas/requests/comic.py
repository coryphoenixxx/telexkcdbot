import datetime as dt

from pydantic import BaseModel, HttpUrl, field_validator
from shared.utils import cast_or_none

from api.application.dtos.requests.comic import ComicRequestDTO
from api.types import IssueNumber, TranslationImageID


class ComicRequestSchema(BaseModel):
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]
    image_ids: list[TranslationImageID]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        result = []
        for tag in tags:
            stripped_tag = tag.strip()
            if len(stripped_tag) < 2:
                raise ValueError(f"`{tag}` is invalid tag. Minimum length is 2.")
            result.append(stripped_tag)
        return result

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            number=self.number,
            title=self.title,
            publication_date=self.publication_date,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            link_on_click=cast_or_none(str, self.link_on_click),
            is_interactive=self.is_interactive,
            tags=self.tags,
            image_ids=self.image_ids,
        )
