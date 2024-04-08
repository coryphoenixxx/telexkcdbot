from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.utils import cast_or_none

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import Language, TranslationImageID


class TranslationRequestSchema(BaseModel):
    language: Language.NON_ENGLISH
    title: str = Field(min_length=1)
    tooltip: str = Field(default="")
    transcript_raw: str = Field(default="")
    translator_comment: str = Field(default="")
    image_ids: list[TranslationImageID]
    source_link: HttpUrl | None

    @field_validator(
        "tooltip",
        "transcript_raw",
        "translator_comment",
        mode="before",
    )
    @classmethod
    def preprocess_text_fields(cls, value: str | None) -> str:
        # TODO: i need default in attrs with this method?
        if value is None:
            value = ""
        return value

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript_raw=self.transcript_raw,
            translator_comment=self.translator_comment,
            image_ids=self.image_ids,
            source_link=cast_or_none(str, self.source_link),
        )
