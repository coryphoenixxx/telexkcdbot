from dataclasses import dataclass

from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.types import ComicID
from api.infrastructure.database.models import ComicModel


@dataclass(slots=True)
class ComicResponseDTO(ComicRequestDTO):
    id: ComicID

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicResponseDTO":
        return ComicResponseDTO(
            id=model.id,
            number=model.number,
            publication_date=model.publication_date,
            xkcd_url=model.xkcd_url,
            explain_url=model.explain_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=sorted([tag.name for tag in model.tags]),
        )


@dataclass(slots=True)
class ComicResponseWithTranslationsDTO(ComicResponseDTO):
    translations: list[TranslationResponseDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicResponseWithTranslationsDTO":
        return ComicResponseWithTranslationsDTO(
            id=model.id,
            number=model.number,
            publication_date=model.publication_date,
            xkcd_url=model.xkcd_url,
            explain_url=model.explain_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=sorted([tag.name for tag in model.tags]),
            translations=[TranslationResponseDTO.from_model(t) for t in model.translations],
        )
