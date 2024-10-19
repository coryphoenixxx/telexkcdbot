from collections.abc import Sequence
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import NoReturn, Protocol

from backend.application.comic.filters import ComicFilters
from backend.application.comic.responses import (
    ComicCompactResponseData,
    ComicResponseData,
    TagResponseData,
    TranslationResponseData,
)
from backend.application.common.pagination import Pagination
from backend.domain.entities import (
    ComicEntity,
    NewComicEntity,
    NewTagEntity,
    NewTranslationEntity,
    TagEntity,
    TranslationEntity,
    TranslationStatus,
)
from backend.domain.value_objects import (
    ComicId,
    ImageId,
    IssueNumber,
    Language,
    TagId,
    TranslationId,
    TranslationTitle,
)


class ComicRepoInterface(Protocol):
    async def create(self, new_comic: NewComicEntity) -> tuple[ComicId, TranslationId]: ...

    async def update(self, comic: ComicEntity) -> None: ...

    async def delete(self, comic_id: ComicId) -> None: ...

    @singledispatchmethod
    async def get_by(self) -> NoReturn: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, comic_id: ComicId) -> ComicResponseData: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, number: IssueNumber) -> ComicResponseData: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, slug: str) -> ComicResponseData: ...

    async def get_list(
        self,
        filters: ComicFilters,
        pagination: Pagination,
    ) -> tuple[int, Sequence[ComicCompactResponseData]]: ...

    async def get_number_and_title_by_id(
        self,
        comic_id: ComicId,
    ) -> tuple[IssueNumber | None, TranslationTitle]: ...

    async def get_latest_issue_number(self) -> IssueNumber | None: ...

    async def get_translations(
        self,
        comic_id: ComicId,
        language: Language | None = None,
        status: TranslationStatus | None = None,
    ) -> list[TranslationResponseData]: ...

    async def relink_tags(self, comic_id: ComicId, tag_ids: Sequence[TagId]) -> None: ...

    async def load(self, comic_id: ComicId) -> ComicEntity: ...


class TagRepoInterface(Protocol):
    async def create(self, tag: NewTagEntity) -> TagId: ...

    async def create_many(self, tags: Sequence[NewTagEntity]) -> Sequence[TagId]: ...

    async def update(self, tag: TagEntity) -> None: ...

    async def delete(self, tag_id: TagId) -> None: ...

    async def get_by_id(self, tag_id: TagId) -> TagResponseData: ...

    async def load(self, tag_id: TagId) -> TagEntity: ...


class TranslationRepoInterface(Protocol):
    async def create(self, translation: NewTranslationEntity) -> TranslationId: ...

    async def update(self, translation: TranslationEntity) -> None: ...

    async def delete(self, translation_id: TranslationId) -> None: ...

    async def get_by_id(self, translation_id: TranslationId) -> TranslationResponseData: ...

    async def load(self, translation_id: TranslationId) -> TranslationEntity: ...


@dataclass(slots=True, kw_only=True)
class TranslationImagePathData:
    number: IssueNumber | None
    original_title_slug: str
    translation_title_slug: str
    language: Language = Language.EN
    status: TranslationStatus = TranslationStatus.PUBLISHED


class TranslationImageSaveHelperInterface(Protocol):
    async def update_image(
        self,
        translation_id: TranslationId,
        old_image_id: ImageId | None,
        new_image_id: ImageId | None,
        path_data: TranslationImagePathData,
        move_image_required: bool,
    ) -> ImageId | None: ...

    async def create_new_image(
        self,
        translation_id: TranslationId,
        image_id: ImageId,
        path_data: TranslationImagePathData,
    ) -> None: ...

    async def move_image(
        self,
        image_id: ImageId,
        new_path_data: TranslationImagePathData,
    ) -> None: ...

    async def soft_delete_image(self, image_id: ImageId | None) -> None: ...

    async def get_linked_image_id(self, translation_id: TranslationId) -> ImageId | None: ...
