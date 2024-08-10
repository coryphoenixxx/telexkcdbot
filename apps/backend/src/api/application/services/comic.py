from shared.my_types import Order

from api.application.dtos.common import ComicFilterParams, Language, Limit, TotalCount
from api.application.dtos.requests import ComicRequestDTO
from api.application.dtos.responses import (
    ComicResponseDTO,
)
from api.application.services.converter import Converter
from api.core.value_objects import ComicID, IssueNumber
from api.infrastructure.database.repositories import (
    ComicRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from api.infrastructure.database.repositories.tag import TagRepo
from api.infrastructure.database.transaction import TransactionManager
from api.infrastructure.filesystem.image_file_manager import ImageFileManager


class ComicService:
    def __init__(
        self,
        transaction: TransactionManager,
        comic_repo: ComicRepo,
        translation_repo: TranslationRepo,
        translation_image_repo: TranslationImageRepo,
        tag_repo: TagRepo,
        image_file_manager: ImageFileManager,
        converter: Converter,
    ) -> None:
        self._transaction = transaction
        self._comic_repo = comic_repo
        self._translation_repo = translation_repo
        self._translation_image_repo = translation_image_repo
        self._tag_repo = tag_repo
        self._image_file_manager = image_file_manager
        self._converter = converter

    async def create(self, dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_id = await self._comic_repo.create_base(dto)
        await self._tag_repo.create_many(comic_id, dto.tags)
        translation = await self._translation_repo.create(comic_id, dto.original)

        image_rel_path = None
        try:
            if dto.image_id:
                image_rel_path = await self._image_file_manager.save(
                    number=dto.number,
                    title=dto.title,
                    language=Language.EN,
                    is_draft=False,
                    temp_image_id=dto.image_id,
                )
                image_dto = await self._translation_image_repo.create(image_rel_path)

                await self._translation_image_repo.attach_image(translation.id, image_dto.id)
                await self._converter.convert(image_dto.id)

            await self._transaction.commit()
        except Exception as err:
            if image_rel_path:
                self._image_file_manager.delete(image_rel_path)
            raise err
        else:
            return await self._comic_repo.get_by_id(comic_id)

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> ComicResponseDTO:
        await self._comic_repo.update_base(comic_id, dto)
        translation = await self._translation_repo.update_original(comic_id, dto.original)
        await self._translation_image_repo.attach_image(translation.id, dto.image_id)
        await self._tag_repo.create_many(comic_id, dto.tags)

        await self._transaction.commit()

        return await self._comic_repo.get_by_id(comic_id)

    async def delete(self, comic_id: ComicID) -> None:
        await self._comic_repo.delete(comic_id)
        await self._transaction.commit()

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self._comic_repo.get_by_id(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self._comic_repo.get_by_issue_number(number)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self._comic_repo.get_by_slug(slug)

    async def get_latest_issue_number(self) -> IssueNumber:
        return (
            await self._comic_repo.get_list(
                filter_params=ComicFilterParams(
                    limit=Limit(1),
                    order=Order.DESC,
                )
            )
        )[1][0].number

    async def get_list(
        self,
        query_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseDTO]]:
        total, comic_resp_dtos = await self._comic_repo.get_list(query_params)

        return total, comic_resp_dtos
