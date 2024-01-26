import datetime as dt

from pydantic import BaseModel, Field, HttpUrl

from api.application.comics.types import ComicID, IssueNumber
from api.application.translations.schemas.response import TranslationResponseSchema


class ComicResponseSchema(BaseModel):
    id: ComicID
    number: IssueNumber | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]


class ComicWithTranslationsResponseSchema(ComicResponseSchema):
    translations: list[TranslationResponseSchema]
