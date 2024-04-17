from pydantic import BaseModel, HttpUrl
from shared.utils import cast_or_none

from api.application.dtos.requests.translation import (
    TranslationRequestDTO,
)
from api.types import Language, TranslationImageID


class TranslationRequestSchema(BaseModel):
    language: Language
    title: str
    tooltip: str
    raw_transcript: str
    translator_comment: str
    image_ids: list[TranslationImageID]
    source_url: HttpUrl | None

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment=self.translator_comment,
            image_ids=self.image_ids,
            source_url=cast_or_none(str, self.source_url),
            is_draft=False,
        )


class TranslationDraftRequestSchema(TranslationRequestSchema):
    def to_dto(self) -> TranslationRequestDTO:
        dto = super().to_dto()
        dto.is_draft = True

        return dto
