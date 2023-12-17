import datetime as dt

from pydantic import BaseModel, HttpUrl

from .dtos import ComicCreateDTO
from .translations.dtos import TranslationCreateDTO


class ComicCreateSchema(BaseModel):
    issue_number: int | None
    title: str
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    is_interactive: bool = False
    is_extra: bool = False
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    tooltip: str | None = None
    transcript: str | None = None
    news_block: str | None = None
    tags: list[str] | None = None

    def to_dtos(self) -> tuple[ComicCreateDTO, TranslationCreateDTO]:
        return ComicCreateDTO(
            issue_number=self.issue_number,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            reddit_url=self.reddit_url,
            is_interactive=self.is_interactive,
            is_extra=self.is_extra,
            link_on_click=self.link_on_click,
            tags=self.tags,
        ), TranslationCreateDTO(
            title=self.title,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news_block=self.news_block,
        )
