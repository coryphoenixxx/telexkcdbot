import datetime as dt
from typing import Annotated
from uuid import UUID

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, HttpUrl, PositiveInt

from backend.application.dtos import ComicRequestDTO, TranslationRequestDTO
from backend.application.services.tag import TagUpdateDTO
from backend.core.value_objects import IssueNumber, Language, TagName, TempFileID
from backend.infrastructure.utils import cast_or_none


class ComicRequestSchema(BaseModel):
    number: PositiveInt | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[Annotated[str, MinLen(2), MaxLen(50)]]
    temp_image_id: UUID

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            number=cast_or_none(IssueNumber, self.number),
            title=self.title,
            publication_date=self.publication_date,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            click_url=cast_or_none(str, self.click_url),
            is_interactive=self.is_interactive,
            tags=[TagName(tag) for tag in self.tags],
            temp_image_id=TempFileID(self.temp_image_id),
        )


class TranslationRequestSchema(BaseModel):
    title: str
    language: Language
    tooltip: str
    raw_transcript: str
    translator_comment: str
    source_url: HttpUrl | None
    temp_image_id: UUID

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=Language(self.language),
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment=self.translator_comment,
            source_url=cast_or_none(str, self.source_url),
            temp_image_id=TempFileID(self.temp_image_id),
            is_draft=False,
        )


class TranslationDraftRequestSchema(TranslationRequestSchema):
    def to_dto(self) -> TranslationRequestDTO:
        dto = super().to_dto()
        dto.is_draft = True
        return dto


class TagUpdateQuerySchema(BaseModel):
    name: Annotated[str, MinLen(2), MaxLen(50)] | None = None
    is_blacklisted: bool | None = None

    def to_dto(self) -> TagUpdateDTO:
        dto = TagUpdateDTO(**self.model_dump(exclude_none=True))

        if hasattr(TagUpdateQuerySchema, "name"):
            dto.name = TagName(dto.name)

        return dto
