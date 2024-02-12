from pydantic import BaseModel, Field, field_validator
from shared.types import LanguageCode

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import ComicID, TranslationImageID


class TranslationRequestSchema(BaseModel):
    comic_id: int
    title: str = Field(min_length=1)
    language: LanguageCode
    tooltip: str = Field(default="")
    transcript_html: str = Field(default="")
    translator_comment: str = Field(default="")
    images: list[int]
    is_draft: bool = Field(default=False)

    @field_validator(
        "tooltip",
        "transcript_html",
        "translator_comment",
        mode="before",
    )
    @classmethod
    def validate_tooltip_transcript(cls, value: str | None):
        if value is None:
            value = ""
        return value

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            comic_id=ComicID(self.comic_id),
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript_html=self.transcript_html,
            translator_comment=self.translator_comment,
            images=[TranslationImageID(img) for img in self.images],
            is_draft=self.is_draft,
        )
