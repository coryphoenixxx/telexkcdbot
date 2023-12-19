import datetime as dt

from pydantic import BaseModel, HttpUrl, model_validator

from .dtos import ComicCreateDTO
from .translations.dtos import TranslationCreateDTO


class ComicCreateSchema(BaseModel):
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    is_interactive: bool = False
    is_extra: bool = False
    tags: list[str] | None = []

    title: str
    tooltip: str | None = None
    transcript: str | None = None
    news_block: str | None = None

    @model_validator(mode="after")
    def check_issue_number_and_is_extra_conflict(self) -> "ComicCreateSchema":
        if self.issue_number and self.is_extra:
            raise ValueError("Extra comics should not have an issue number.")
        if not self.issue_number and not self.is_extra:
            raise ValueError("Comics without an issue number cannot be not extra.")
        return self

    def to_dto(self) -> ComicCreateDTO:
        return ComicCreateDTO(
            issue_number=self.issue_number,
            publication_date=self.publication_date,
            xkcd_url=str(self.xkcd_url),
            explain_url=str(self.explain_url),
            reddit_url=str(self.reddit_url),
            link_on_click=str(self.link_on_click),
            is_interactive=self.is_interactive,
            is_extra=self.is_extra,
            tags=list(set(self.tags)),
            translation=TranslationCreateDTO(
                title=self.title,
                tooltip=self.tooltip,
                transcript=self.transcript,
                news_block=self.news_block,
            ),
        )
