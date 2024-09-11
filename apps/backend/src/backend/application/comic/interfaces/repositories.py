from collections.abc import Sequence
from functools import singledispatchmethod
from pathlib import Path
from typing import Any, NoReturn, Protocol

from backend.application.comic.dtos import (
    ComicRequestDTO,
    ComicResponseDTO,
    TagResponseDTO,
    TranslationImageRequestDTO,
    TranslationImageResponseDTO,
    TranslationRequestDTO,
    TranslationResponseDTO,
)
from backend.application.common.pagination import ComicFilterParams, TotalCount
from backend.core.value_objects import (
    ComicID,
    IssueNumber,
    Language,
    TagID,
    TagName,
    TranslationID,
    TranslationImageID,
)


class ComicRepoInterface(Protocol):
    async def create(self, dto: ComicRequestDTO) -> ComicID: ...

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> None: ...

    async def delete(self, comic_id: ComicID) -> None: ...

    @singledispatchmethod
    async def get_by(self) -> NoReturn: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: ComicID) -> ComicResponseDTO: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: IssueNumber) -> ComicResponseDTO: ...

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: str) -> ComicResponseDTO: ...

    async def get_list(
        self,
        filter_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseDTO]]: ...

    async def get_issue_number_by_id(self, comic_id: ComicID) -> IssueNumber | None: ...

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]: ...


class TagRepoInterface(Protocol):
    async def create_many(
        self,
        comic_id: ComicID,
        tag_names: Sequence[TagName],
    ) -> Sequence[TagResponseDTO]: ...

    async def update(self, tag_id: TagID, data: dict[str, Any]) -> TagResponseDTO: ...

    async def delete(self, tag_id: TagID) -> None: ...

    async def get_by_id(self, tag_id: TagID) -> TagResponseDTO: ...


class TranslationRepoInterface(Protocol):
    async def create(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO: ...

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO: ...

    async def update_original(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO: ...

    async def update_draft_status(
        self,
        translation_id: TranslationID,
        new_draft_status: bool,
    ) -> None: ...
    async def delete(self, translation_id: TranslationID) -> None: ...

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO: ...

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO | None: ...


class TranslationImageRepoInterface(Protocol):
    async def create(self, dto: TranslationImageRequestDTO) -> TranslationImageResponseDTO: ...

    async def update_converted(
        self,
        image_id: TranslationImageID,
        converted_rel_path: Path,
    ) -> None: ...

    async def get_by_id(
        self,
        image_id: TranslationImageID,
    ) -> TranslationImageResponseDTO | None: ...
