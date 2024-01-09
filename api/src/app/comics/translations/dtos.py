from dataclasses import dataclass

from src.app.comics.images.dtos import TranslationImageGetDTO
from src.app.comics.images.types import TranslationImageID, TranslationImageVersion
from src.app.comics.translations.models import TranslationModel
from src.app.comics.translations.types import TranslationID
from src.core.types import Language


@dataclass(slots=True)
class TranslationCreateDTO:
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    language: Language = Language.EN
    is_draft: bool = False
    comic_id: int | None = None


@dataclass(slots=True)
class TranslationGetDTO:
    id: TranslationID
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[TranslationImageVersion, dict[str, str | None]]
    is_draft: bool = False

    @classmethod
    def from_model(cls, model: TranslationModel):
        images = {}
        for img in model.images:
            images = images | TranslationImageGetDTO.from_model(img)

        return {
            model.language: TranslationGetDTO(
                id=model.id,
                title=model.title,
                tooltip=model.tooltip,
                transcript=model.transcript,
                news_block=model.news_block,
                images=images,
                is_draft=model.is_draft,
            ),
        }
