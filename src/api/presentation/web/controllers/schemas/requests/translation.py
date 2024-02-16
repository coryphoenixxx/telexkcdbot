from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.types import LanguageCode
from shared.utils import cast_or_none

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import ComicID, TranslationImageID


class TranslationRequestSchema(BaseModel):
    comic_id: int
    language: LanguageCode
    title: str = Field(min_length=1)
    tooltip: str = Field(default="")
    transcript_raw: str = Field(default="")
    translator_comment: str = Field(default="")
    images: list[int]
    source_link: HttpUrl | None
    is_draft: bool = Field(default=False)

    @field_validator(
        "tooltip",
        "transcript_raw",
        "translator_comment",
        mode="before",
    )
    @classmethod
    def preprocess_text_fields(cls, value: str | None):
        if value is None:
            value = ""
        return value

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            comic_id=ComicID(self.comic_id),
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript_raw=self.transcript_raw,
            translator_comment=self.translator_comment,
            images=[TranslationImageID(img) for img in self.images],
            source_link=cast_or_none(str, self.source_link),
            is_draft=self.is_draft,
        )
