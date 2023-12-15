import datetime

from pydantic import BaseModel, HttpUrl

from .dtos import ComicCreateDTO


class ComicCreateSchema(BaseModel):
    comic_id: int
    title: str
    publication_date: datetime.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    is_interactive: bool = False
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    tooltip: str | None = None
    transcript: str | None = None
    news_block: str | None = None
    tags: list[str] | None = None

    def to_dto(self) -> ComicCreateDTO:
        return ComicCreateDTO(**self.model_dump())
