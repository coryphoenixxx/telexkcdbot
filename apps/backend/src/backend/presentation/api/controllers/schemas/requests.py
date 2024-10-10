import datetime as dt

from pydantic import BaseModel, HttpUrl

from backend.application.comic.commands import (
    ComicCreateCommand,
    ComicUpdateCommand,
    TagCreateCommand,
    TagUpdateCommand,
    TranslationCreateCommand,
    TranslationUpdateCommand,
)
from backend.domain.entities import TranslationStatus
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import Language


class ComicCreateSchema(BaseModel):
    number: int | None
    title: str
    publication_date: dt.date
    tooltip: str
    transcript: str
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl | None
    click_url: HttpUrl | None
    is_interactive: bool
    tag_ids: list[int]
    image_ids: list[int]

    def to_command(self) -> ComicCreateCommand:
        return ComicCreateCommand(
            number=self.number,
            publication_date=self.publication_date,
            explain_url=cast_or_none(str, self.explain_url),
            click_url=cast_or_none(str, self.click_url),
            is_interactive=self.is_interactive,
            title=self.title,
            tooltip=self.tooltip,
            transcript=self.transcript,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            tag_ids=self.tag_ids,
            image_ids=self.image_ids,
        )


class ComicUpdateSchema(BaseModel):
    number: int | None = None
    title: str | None = None
    tooltip: str | None = None
    click_url: HttpUrl | None = None
    explain_url: HttpUrl | None = None
    is_interactive: bool | None = None
    transcript: str | None = None
    tag_ids: list[int] | None = None
    image_ids: list[int]

    def to_command(self, comic_id: int) -> ComicUpdateCommand:
        return ComicUpdateCommand(  # type: ignore[no-any-return]
            comic_id=comic_id,
            **self.model_dump(exclude_unset=True),  # type: ignore[typeddict-item]
        )


class TranslationCreateSchema(BaseModel):
    language: str
    title: str
    tooltip: str
    transcript: str
    translator_comment: str
    source_url: HttpUrl | None
    status: TranslationStatus
    image_ids: list[int]

    def to_command(self, comic_id: int) -> TranslationCreateCommand:
        return TranslationCreateCommand(
            comic_id=comic_id,
            language=Language(self.language),
            title=self.title,
            tooltip=self.tooltip,
            transcript=self.transcript,
            translator_comment=self.translator_comment,
            source_url=cast_or_none(str, self.source_url),
            status=self.status,
            image_ids=self.image_ids,
        )


class TranslationUpdateSchema(BaseModel):
    language: Language | None = None
    title: str | None = None
    tooltip: str | None = None
    transcript: str | None = None
    translator_comment: str | None = None
    source_url: str | None = None
    status: TranslationStatus | None = None
    image_ids: list[int]

    def to_command(self, translation_id: int) -> TranslationUpdateCommand:
        return TranslationUpdateCommand(  # type: ignore[no-any-return]
            translation_id=translation_id,
            **self.model_dump(exclude_unset=True),  # type: ignore[typeddict-item]
        )


class TagCreateSchema(BaseModel):
    name: str

    def to_command(self) -> TagCreateCommand:
        return TagCreateCommand(
            name=self.name,
            is_visible=True,
            from_explainxkcd=False,
        )


class TagUpdateSchema(BaseModel):
    name: str | None = None
    is_visible: bool | None = None

    def to_command(self, tag_id: int) -> TagUpdateCommand:
        return TagUpdateCommand(  # type: ignore[no-any-return]
            tag_id=tag_id,
            **self.model_dump(exclude_unset=True),  # type: ignore[typeddict-item]
        )
