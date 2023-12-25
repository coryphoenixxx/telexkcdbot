import datetime as dt

from pydantic import BaseModel, HttpUrl, field_validator, model_validator


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

    @field_validator("tags")
    @classmethod
    def check_tags(cls, tags: list[str] | None) -> list[str] | None:
        if tags:
            for tag in tags:
                if not tag.strip() or len(tag) < 3:
                    raise ValueError(f"Tag №{tags.index(tag) + 1} is invalid.")
            return list({tag.strip() for tag in tags})

    @model_validator(mode="after")
    def check_issue_number_and_is_extra_conflict(self) -> "ComicCreateSchema":
        if self.issue_number and self.is_extra:
            raise ValueError("Extra comics should not have an issue number.")
        if not self.issue_number and not self.is_extra:
            raise ValueError("Comics without an issue number cannot be not extra.")
        return self
