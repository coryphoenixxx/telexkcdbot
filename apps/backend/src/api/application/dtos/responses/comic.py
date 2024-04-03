from dataclasses import dataclass
from datetime import datetime as dt

from api.application.dtos.responses import (
    TranslationImageProcessedResponseDTO,
    TranslationResponseDTO,
)
from api.application.types import ComicID, IssueNumber
from api.infrastructure.database.models import ComicModel


@dataclass(slots=True)
class ComicResponseDTO:
    id: ComicID
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    transcript_raw: str
    xkcd_url: str | None
    explain_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]
    images: list[TranslationImageProcessedResponseDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicResponseDTO":
        return ComicResponseDTO(
            id=model.comic_id,
            number=model.number,
            title=model.en_translation.title,
            publication_date=model.publication_date,
            tooltip=model.en_translation.tooltip,
            transcript_raw=model.en_translation.transcript_raw,
            xkcd_url=model.en_translation.source_link,
            explain_url=model.explain_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=sorted([tag.name for tag in model.tags]),  # TODO: sort by SQL?
            images=model.en_translation.images,
        )


@dataclass(slots=True)
class ComicResponseWTranslationsDTO(ComicResponseDTO):
    translations: list[TranslationResponseDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicResponseWTranslationsDTO":
        return ComicResponseWTranslationsDTO(
            id=model.comic_id,
            number=model.number,
            title=model.en_translation.title,
            publication_date=model.publication_date,
            tooltip=model.en_translation.tooltip,
            transcript_raw=model.en_translation.transcript_raw,
            xkcd_url=model.en_translation.source_link,
            explain_url=model.explain_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=sorted([tag.name for tag in model.tags]),  # TODO: sort by SQL?
            images=[
                TranslationImageProcessedResponseDTO.from_model(img)
                for img in model.en_translation.images
            ],
            translations=[TranslationResponseDTO.from_model(t) for t in model.translations],
        )
