from dataclasses import dataclass, field
from datetime import datetime as dt

from src.core.utils import cast_or_none

from .image_utils.dtos import ComicImageDTO, ImageDTO
from .image_utils.types import ImageTypeEnum
from .models import ComicModel
from .schemas import ComicCreateSchema
from .translations.dtos import TranslationCreateDTO, TranslationGetDTO


@dataclass(slots=True)
class ComicCreateDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    is_extra: bool
    tags: list[str]


@dataclass(slots=True)
class ComicTotalDTO:
    issue_number: int | None
    comic: ComicCreateDTO
    translation: TranslationCreateDTO
    images: list[ComicImageDTO] = field(default_factory=list)

    @classmethod
    def from_request_data(
        cls,
        comic_create_schema: ComicCreateSchema,
        image_obj: ImageDTO | None,
        image_2x_obj: ImageDTO | None,
    ) -> "ComicTotalDTO":
        comic_dto = ComicTotalDTO(
            issue_number=comic_create_schema.issue_number,
            comic=ComicCreateDTO(
                issue_number=comic_create_schema.issue_number,
                publication_date=comic_create_schema.publication_date,
                xkcd_url=cast_or_none(str, comic_create_schema.xkcd_url),
                explain_url=cast_or_none(str, comic_create_schema.explain_url),
                reddit_url=cast_or_none(str, comic_create_schema.reddit_url),
                link_on_click=cast_or_none(str, comic_create_schema.link_on_click),
                is_interactive=comic_create_schema.is_interactive,
                is_extra=comic_create_schema.is_extra,
                tags=comic_create_schema.tags,
            ),
            translation=TranslationCreateDTO(
                issue_number=comic_create_schema.issue_number,
                title=comic_create_schema.title,
                tooltip=comic_create_schema.tooltip,
                transcript=comic_create_schema.transcript,
                news_block=comic_create_schema.news_block,
            ),
        )

        if image_obj:
            comic_dto.images.append(
                ComicImageDTO(
                    issue_number=comic_dto.issue_number,
                    path=image_obj.path,
                    format_=image_obj.format_,
                    size=image_obj.size,
                ),
            )
        if image_2x_obj:
            comic_dto.images.append(
                ComicImageDTO(
                    issue_number=comic_dto.issue_number,
                    path=image_2x_obj.path,
                    format_=image_2x_obj.format_,
                    size=image_2x_obj.size,
                    type_=ImageTypeEnum.ENLARGED,
                ),
            )

        for img in comic_dto.images:
            if img:
                comic_dto.translation.images[img.type_] = img.rel_path

        return comic_dto


@dataclass(slots=True)
class ComicGetDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    is_extra: bool
    tags: list[str]
    translations: dict[str, TranslationGetDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicGetDTO":
        translations = {}
        for tr in model.translations:
            translations[tr.language] = TranslationGetDTO(
                title=tr.title,
                tooltip=tr.tooltip,
                transcript=tr.transcript,
                news_block=tr.news_block,
                images=tr.images,
                is_draft=tr.is_draft,
            )
        return cls(
            issue_number=model.issue_number,
            publication_date=model.publication_date,
            xkcd_url=model.xkcd_url,
            explain_url=model.explain_url,
            reddit_url=model.reddit_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            is_extra=model.is_extra,
            tags=[tag.name for tag in model.tags],
            translations=translations,
        )
