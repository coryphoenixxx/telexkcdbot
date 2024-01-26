from dataclasses import dataclass

from api.application.comics.dtos.request import ComicRequestDTO
from api.application.comics.schemas.response import (
    ComicResponseSchema,
    ComicWithTranslationsResponseSchema,
)
from api.application.comics.types import ComicID
from api.application.translations.dtos.response import TranslationResponseDTO
from api.application.translations.schemas.response import TranslationResponseSchema


@dataclass(slots=True)
class ComicResponseDTO(ComicRequestDTO):
    id: ComicID

    def to_schema(self) -> ComicResponseSchema:
        return ComicResponseSchema(
            id=self.id,
            number=self.number,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            link_on_click=self.link_on_click,
            is_interactive=self.is_interactive,
            tags=self.tags,
        )


@dataclass(slots=True)
class ComicResponseWithTranslationsDTO(ComicResponseDTO):
    translations: list[TranslationResponseDTO]

    def to_schema(self) -> ComicWithTranslationsResponseSchema:
        translations = []
        for t in self.translations:
            images_dict = {}
            for image in t.images:
                images_dict = images_dict | image.as_dict()

            translations.append(
                TranslationResponseSchema(
                    id=t.id,
                    comic_id=t.comic_id,
                    title=t.title,
                    language=t.language,
                    tooltip=t.tooltip,
                    transcript=t.transcript,
                    images=images_dict,
                    is_draft=t.is_draft,
                ),
            )

        return ComicWithTranslationsResponseSchema(
            id=self.id,
            number=self.number,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            link_on_click=self.link_on_click,
            is_interactive=self.is_interactive,
            tags=self.tags,
            translations=translations,
        )
