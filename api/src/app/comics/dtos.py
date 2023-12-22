from dataclasses import asdict, dataclass, field
from datetime import datetime as dt

from .image_utils.dtos import ComicImageDTO
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
    comic: ComicCreateDTO
    translation: TranslationCreateDTO
    images: list[ComicImageDTO | None] = field(default_factory=list)
    issue_number: int | None = None

    def __setattr__(self, key, value):
        if key == 'issue_number' and value:
            self.comic.issue_number = value
            self.translation.issue_number = value
            for img in self.images:
                if img:
                    img.issue_number = value
                    self.translation.images[img.type_] = img.db_path
        object.__setattr__(self, key, value)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_request(
            cls,
            comic_create_schema: ComicCreateSchema,
            image_obj,
            image_2x_obj,
    ) -> "ComicTotalDTO":
        return ComicTotalDTO(
            comic=ComicCreateDTO(
                issue_number=comic_create_schema.issue_number,
                publication_date=comic_create_schema.publication_date,
                xkcd_url=str(comic_create_schema.xkcd_url),
                explain_url=str(comic_create_schema.explain_url),
                reddit_url=str(comic_create_schema.reddit_url),
                link_on_click=str(comic_create_schema.link_on_click),
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
            images=[
                ComicImageDTO(**asdict(image_obj)) if image_obj else None,
                ComicImageDTO(**asdict(image_2x_obj), type_=ImageTypeEnum.ENLARGED) if image_2x_obj else None,
            ],
            issue_number=comic_create_schema.issue_number,
        )


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
