from dataclasses import dataclass

from backend.application.comic.dtos import (
    ComicRequestDTO,
    ComicResponseDTO,
    TranslationResponseDTO,
)
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TagRepoInterface,
    TranslationRepoInterface,
)
from backend.application.common.interfaces import (
    TransactionManagerInterface,
)
from backend.application.common.pagination import ComicFilterParams, Limit, Order, TotalCount
from backend.core.value_objects import ComicID, IssueNumber

from .mixins import ProcessTranslationImageMixin


@dataclass(slots=True)
class CreateComicInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_id = await self.comic_repo.create(dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        original_translation = dto.original_translation
        translation = await self.translation_repo.create(comic_id, original_translation)
        image = await self.create_image(translation.id, dto.number, original_translation)

        await self.transaction.commit()

        await self.process_image_in_background(
            temp_image_id=original_translation.temp_image_id,
            image_dto=image,
        )

        return await self.comic_repo.get_by(comic_id)


@dataclass(slots=True)
class FullUpdateComicInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, comic_id: ComicID, dto: ComicRequestDTO) -> ComicResponseDTO:
        await self.comic_repo.update(comic_id, dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        original_translation = dto.original_translation
        translation = await self.translation_repo.update_original(
            comic_id=comic_id,
            dto=original_translation,
        )
        image = await self.create_image(translation.id, dto.number, original_translation)

        await self.transaction.commit()

        await self.process_image_in_background(
            temp_image_id=original_translation.temp_image_id,
            image_dto=image,
        )

        return await self.comic_repo.get_by(comic_id)


@dataclass(slots=True)
class DeleteComicInteractor:
    comic_repo: ComicRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, comic_id: ComicID) -> None:
        await self.comic_repo.delete(comic_id)
        await self.transaction.commit()


@dataclass(slots=True)
class ComicReader:
    comic_repo: ComicRepoInterface

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self.comic_repo.get_by(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self.comic_repo.get_by(number)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self.comic_repo.get_by(slug)

    async def get_latest_issue_number(self) -> IssueNumber | None:
        _, comics = await self.comic_repo.get_list(
            filter_params=ComicFilterParams(
                limit=Limit(1),
                order=Order.DESC,
            )
        )

        if comics:
            return comics[0].number
        return None

    async def get_list(
        self,
        query_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseDTO]]:
        return await self.comic_repo.get_list(query_params)

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        return await self.comic_repo.get_translations(comic_id)
