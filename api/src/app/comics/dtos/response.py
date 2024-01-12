from dataclasses import dataclass

from src.app.comics.dtos.request import ComicRequestDTO
from src.app.comics.schemas.response import (
    ComicResponseSchema,
    ComicWithTranslationsResponseSchema,
)
from src.app.comics.types import ComicID
from src.app.translations.dtos.response import TranslationResponseDTO
from src.app.translations.schemas.response import TranslationResponseSchema


@dataclass(slots=True)
class ComicResponseDTO(ComicRequestDTO):
    id: ComicID

    def to_schema(self) -> ComicResponseSchema:
        return ComicResponseSchema(
            id=self.id,
            issue_number=self.issue_number,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            reddit_url=self.reddit_url,
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
            image_dict = {}
            for image in t.images:
                image_dict[image.version] = {
                    "id": image.id,
                    "path": image.path,
                    "converted": image.converted_path,
                }

            translations.append(
                TranslationResponseSchema(
                    id=t.id,
                    title=t.title,
                    language=t.language,
                    tooltip=t.tooltip,
                    transcript=t.transcript,
                    news_block=t.news_block,
                    images=image_dict,
                    is_draft=t.is_draft,
                ),
            )

        return ComicWithTranslationsResponseSchema(
            id=self.id,
            issue_number=self.issue_number,
            publication_date=self.publication_date,
            xkcd_url=self.xkcd_url,
            explain_url=self.explain_url,
            reddit_url=self.reddit_url,
            link_on_click=self.link_on_click,
            is_interactive=self.is_interactive,
            tags=self.tags,
            translations=translations,
        )
