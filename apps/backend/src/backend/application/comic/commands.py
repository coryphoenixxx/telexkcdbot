import datetime as dt
from dataclasses import dataclass
from typing import Required, TypedDict

from backend.domain.entities import (
    NewComicEntity,
    NewTagEntity,
    NewTranslationEntity,
    TranslationStatus,
)
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import (
    ComicId,
    ImageId,
    IssueNumber,
    Language,
    TagId,
    TagName,
    TranslationTitle,
)


@dataclass(slots=True, kw_only=True)
class ComicCreateCommand:
    number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    click_url: str | None
    is_interactive: bool
    title: str
    tooltip: str
    transcript: str
    tag_ids: list[int]
    image_ids: list[int]

    def unpack(self) -> tuple[NewComicEntity, list[TagId], list[ImageId]]:
        return (
            NewComicEntity(
                number=cast_or_none(IssueNumber, self.number),
                publication_date=self.publication_date,
                xkcd_url=self.xkcd_url,
                explain_url=self.explain_url,
                click_url=self.click_url,
                is_interactive=self.is_interactive,
                title=TranslationTitle(self.title),
                tooltip=self.tooltip,
                transcript=self.transcript,
            ),
            [TagId(tag_id) for tag_id in self.tag_ids],
            [ImageId(image_id) for image_id in self.image_ids],
        )


class ComicUpdateCommand(TypedDict, total=False):
    comic_id: Required[int]
    image_ids: Required[list[int]]
    number: int | None
    title: str
    tooltip: str
    click_url: str | None
    explain_url: str | None
    is_interactive: bool
    transcript: str
    tag_ids: list[int]


@dataclass(slots=True, kw_only=True)
class TranslationCreateCommand:
    comic_id: int
    language: Language
    title: str
    tooltip: str
    transcript: str
    translator_comment: str
    source_url: str | None
    status: TranslationStatus
    image_ids: list[int]

    def unpack(self) -> tuple[NewTranslationEntity, list[ImageId]]:
        return (
            NewTranslationEntity(
                comic_id=ComicId(self.comic_id),
                title=TranslationTitle(self.title),
                language=self.language,
                tooltip=self.tooltip,
                transcript=self.transcript,
                translator_comment=self.translator_comment,
                source_url=self.source_url,
                status=self.status,
            ),
            [ImageId(image_id) for image_id in self.image_ids],
        )


class TranslationUpdateCommand(TypedDict, total=False):
    translation_id: Required[int]
    image_ids: Required[list[int]]
    language: Language
    title: str
    tooltip: str
    transcript: str
    translator_comment: str
    source_url: str | None
    status: TranslationStatus


@dataclass(slots=True, kw_only=True)
class TagCreateCommand:
    name: str
    is_visible: bool
    from_explainxkcd: bool

    def to_entity(self) -> NewTagEntity:
        return NewTagEntity(
            name=TagName(self.name),
            is_visible=self.is_visible,
            from_explainxkcd=self.from_explainxkcd,
        )


class TagUpdateCommand(TypedDict, total=False):
    tag_id: Required[int]
    name: str
    is_visible: bool
