import datetime as dt

from pydantic import BaseModel, Field, HttpUrl

from src.app.comics.types import ComicID
from src.app.translations.schemas import TranslationResponseSchema


class ComicResponseSchema(BaseModel):
    id: ComicID
    issue_number: int | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    reddit_url: HttpUrl | None
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]


class ComicWithTranslationsResponseSchema(ComicResponseSchema):
    translations: list[TranslationResponseSchema]
