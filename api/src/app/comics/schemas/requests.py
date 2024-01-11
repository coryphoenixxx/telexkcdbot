import datetime as dt

from pydantic import BaseModel, Field, HttpUrl, field_validator

from src.app.comics.dtos.requests import ComicRequestDTO
from src.app.images.types import TranslationImageID
from src.app.translations.dtos import TranslationRequestDTO
from src.core.types import Language
from src.core.utils import cast_or_none


class ComicRequestSchema(BaseModel):
    issue_number: int | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    is_interactive: bool = False
    tags: list[str]

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            issue_number=self.issue_number,
            publication_date=self.publication_date,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            reddit_url=cast_or_none(str, self.reddit_url),
            link_on_click=cast_or_none(str, self.link_on_click),
            is_interactive=self.is_interactive,
            tags=self.tags,
        )


class ComicWithEnTranslationRequestSchema(ComicRequestSchema):
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str] | None:
        if tags:
            for tag in tags:
                if not tag.strip() or len(tag) < 3:
                    raise ValueError(f"Tag №{tags.index(tag) + 1} is invalid.")
        return list({tag.strip() for tag in tags})

    def to_dtos(self) -> tuple[ComicRequestDTO, TranslationRequestDTO]:
        return (
            ComicRequestDTO(
                issue_number=self.issue_number,
                publication_date=self.publication_date,
                xkcd_url=cast_or_none(str, self.xkcd_url),
                explain_url=cast_or_none(str, self.explain_url),
                reddit_url=cast_or_none(str, self.reddit_url),
                link_on_click=cast_or_none(str, self.link_on_click),
                is_interactive=self.is_interactive,
                tags=self.tags,
            ),
            TranslationRequestDTO(
                title=self.title,
                language=Language.EN,
                tooltip=self.tooltip,
                transcript=self.transcript,
                news_block=self.news_block,
                images=self.images,
                is_draft=False,
            ),
        )
