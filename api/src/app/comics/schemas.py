import datetime as dt

from pydantic import BaseModel, Field, HttpUrl, field_validator

from src.app.comics.dtos import ComicGetDTO
from src.app.comics.translations.schemas import TranslationCreateSchema, TranslationGetSchema
from src.app.comics.types import ComicID
from src.core.types import Language


class ComicCreateSchema(BaseModel):
    issue_number: int | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    reddit_url: HttpUrl | None = None
    link_on_click: HttpUrl | None = None
    is_interactive: bool = False
    tags: list[str]
    en_translation: TranslationCreateSchema

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str] | None:
        if tags:
            for tag in tags:
                if not tag.strip() or len(tag) < 3:
                    raise ValueError(f"Tag №{tags.index(tag) + 1} is invalid.")
        return list({tag.strip() for tag in tags})


class ComicGetSchema(BaseModel):
    id: ComicID
    issue_number: int | None = Field(gt=0)
    publication_date: dt.date
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    reddit_url: HttpUrl | None
    link_on_click: HttpUrl | None
    is_interactive: bool
    tags: list[str]
    translations: dict[Language, TranslationGetSchema]

    @classmethod
    def from_dto(cls, dto: ComicGetDTO):
        translations = {}
        for lang, data in dto.translations.items():
            translations[lang] = TranslationGetSchema.from_dto(data)

        return ComicGetSchema(
            id=dto.id,
            issue_number=dto.issue_number,
            publication_date=dto.publication_date,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            reddit_url=dto.reddit_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=dto.tags,
            translations=translations,
        )
