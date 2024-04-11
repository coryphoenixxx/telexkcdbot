from pydantic import BaseModel, HttpUrl, field_validator
from shared.utils import cast_or_none

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.types import Language, TranslationImageID


class TranslationRequestSchema(BaseModel):
    language: Language
    title: str
    tooltip: str | None
    raw_transcript: str
    translator_comment: str
    image_ids: list[TranslationImageID]
    source_link: HttpUrl | None
    is_draft: bool = False

    @field_validator("language", mode="before")
    @classmethod
    def _forbid_english(cls, value: Language) -> Language:
        if value == Language.EN:
            raise ValueError("creating an English translation or translation draft is forbidden.")
        return value

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment=self.translator_comment,
            image_ids=self.image_ids,
            source_link=cast_or_none(str, self.source_link),
            is_draft=self.is_draft,
        )
