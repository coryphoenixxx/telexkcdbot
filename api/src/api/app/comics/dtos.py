from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .translations.dtos import ComicTranslationCreateDTO


@dataclass(slots=True)
class ComicBaseCreateDTO:
    comic_id: int
    publication_date: str
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    is_interactive: bool
    link_on_click: str | None
    tags: list[str] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ComicCreateDTO:
    comic_id: int
    title: str
    publication_date: datetime.date
    is_interactive: bool
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    tags: list[str] | None

    @property
    def base(self):
        return ComicBaseCreateDTO(
            comic_id=self.comic_id,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            reddit_url=self.reddit_url,
            is_interactive=self.is_interactive,
            link_on_click=self.link_on_click,
            tags=self.tags,
        )

    @property
    def translation(self):
        return ComicTranslationCreateDTO(
            comic_id=self.comic_id,
            title=self.title,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news_block=self.news_block,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
