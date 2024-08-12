import datetime as dt

from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic.types import SecretType
from shared.utils import cast_or_none

from api.application.dtos.common import Language, TagName
from api.application.dtos.requests import ComicRequestDTO, TranslationRequestDTO
from api.core.value_objects import IssueNumber, TempImageUUID


class ComicRequestSchema(BaseModel):
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: HttpUrl | None
    explain_url: HttpUrl
    click_url: HttpUrl | None
    is_interactive: bool
    tags: list[TagName]
    image_id: TempImageUUID | None

    def to_dto(self) -> ComicRequestDTO:
        return ComicRequestDTO(
            number=self.number,
            title=self.title,
            publication_date=self.publication_date,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            xkcd_url=cast_or_none(str, self.xkcd_url),
            explain_url=cast_or_none(str, self.explain_url),
            click_url=cast_or_none(str, self.click_url),
            is_interactive=self.is_interactive,
            tags=self.tags,
            image_id=self.image_id,
        )


class TranslationRequestSchema(BaseModel):
    language: Language
    title: str
    tooltip: str
    raw_transcript: str
    translator_comment: str
    image_id: TempImageUUID
    source_url: HttpUrl | None

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment=self.translator_comment,
            image_id=self.image_id,
            source_url=cast_or_none(str, self.source_url),
            is_draft=False,
        )


class TranslationDraftRequestSchema(TranslationRequestSchema):
    def to_dto(self) -> TranslationRequestDTO:
        dto = super().to_dto()
        dto.is_draft = True

        return dto


class UserRequestSchema(BaseModel):
    username: str
    raw_password: SecretStr

    @property
    def secret(self) -> SecretType:
        return self.raw_password.get_secret_value()
