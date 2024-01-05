import datetime as dt

from pydantic import BaseModel, HttpUrl, field_validator


class ComicCreateSchema(BaseModel):
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    is_interactive: bool = False
    tags: list[str]

    title: str
    tooltip: str | None = None
    transcript: str | None = None
    news_block: str | None = None
    image_ids: list[int] = []

    @field_validator("tags")
    @classmethod
    def check_tags(cls, tags: list[str]) -> list[str] | None:
        if tags:
            for tag in tags:
                if not tag.strip() or len(tag) < 3:
                    raise ValueError(f"Tag №{tags.index(tag) + 1} is invalid.")
            return list({tag.strip() for tag in tags})
        return tags
