import datetime as dt

from pydantic import BaseModel, HttpUrl
from shared.utils import cast_or_none

from api.application.dtos.requests.comic import ComicRequestDTO
from api.types import IssueNumber, Tag, TranslationImageID


class ComicRequestSchema(BaseModel):
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[Tag]
    image_ids: list[TranslationImageID]

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            number=self.number,
            title=self.title,
            publication_date=self.publication_date,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            click_url=cast_or_none(str, self.click_url),
            is_interactive=self.is_interactive,
            tags=self.tags,
            image_ids=self.image_ids,
        )
