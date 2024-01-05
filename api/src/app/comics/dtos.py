from dataclasses import dataclass
from datetime import datetime as dt

from src.core.utils import cast_or_none

from .models import ComicModel
from .schemas import ComicCreateSchema
from .translations.dtos import TranslationCreateDTO, TranslationGetDTO


@dataclass(slots=True)
class ComicCreateBaseDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]


@dataclass(slots=True)
class ComicCreateTotalDTO:
    comic_base: ComicCreateBaseDTO
    en_translation: TranslationCreateDTO

    @classmethod
    def from_request(
            cls,
            comic_create_schema: ComicCreateSchema,
    ) -> "ComicCreateTotalDTO":
        return ComicCreateTotalDTO(
            comic_base=ComicCreateBaseDTO(
                issue_number=comic_create_schema.issue_number,
                publication_date=comic_create_schema.publication_date,
                xkcd_url=cast_or_none(str, comic_create_schema.xkcd_url),
                explain_url=cast_or_none(str, comic_create_schema.explain_url),
                reddit_url=cast_or_none(str, comic_create_schema.reddit_url),
                link_on_click=cast_or_none(str, comic_create_schema.link_on_click),
                is_interactive=comic_create_schema.is_interactive,
                tags=comic_create_schema.tags,
            ),
            en_translation=TranslationCreateDTO(
                title=comic_create_schema.title,
                tooltip=comic_create_schema.tooltip,
                transcript=comic_create_schema.transcript,
                news_block=comic_create_schema.news_block,
                image_ids=comic_create_schema.image_ids,
            ),
        )


@dataclass(slots=True)
class ComicGetDTO:
    id: int
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]
    translations: dict[str, TranslationGetDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicGetDTO":
        translations = {}
        for tr in model.translations:
            images = {}

            for img in tr.images:
                images[img.version] = {
                    "dimensions": (img.dimensions.width, img.dimensions.height),
                    "path": img.path,
                    "converted": img.converted_path,
                }

            translations[tr.language] = TranslationGetDTO(
                id=tr.id,
                title=tr.title,
                tooltip=tr.tooltip,
                transcript=tr.transcript,
                news_block=tr.news_block,
                images=images,
                is_draft=tr.is_draft,
            )

        return ComicGetDTO(
            id=model.id,
            issue_number=model.issue_number,
            publication_date=model.publication_date,
            xkcd_url=model.xkcd_url,
            explain_url=model.explain_url,
            reddit_url=model.reddit_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=[tag.name for tag in model.tags],
            translations=translations,
        )
