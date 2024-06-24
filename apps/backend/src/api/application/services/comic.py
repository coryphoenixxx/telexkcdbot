from shared.my_types import Order

from api.application.dtos.common import ComicFilterParams, Limit, TotalCount
from api.application.dtos.requests import ComicRequestDTO
from api.application.dtos.responses import (
    ComicResponseDTO,
)
from api.core.value_objects import ComicID, IssueNumber
from api.infrastructure.database.gateways import (
    ComicGateway,
    TranslationGateway,
    TranslationImageGateway,
)
from api.infrastructure.database.transaction import TransactionManager


class ComicService:
    def __init__(
        self,
        transaction: TransactionManager,
        comic_gateway: ComicGateway,
        translation_gateway: TranslationGateway,
        translation_image_gateway: TranslationImageGateway,
    ) -> None:
        self._transaction = transaction
        self._comic_gateway = comic_gateway
        self._translation_gateway = translation_gateway
        self._translation_image_gateway = translation_image_gateway

    async def create(self, dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_id = await self._comic_gateway.create_base(dto)
        translation = await self._translation_gateway.create(comic_id, dto.original)
        await self._translation_image_gateway.link(translation.id, dto.image_ids)

        await self._transaction.commit()

        return await self._comic_gateway.get_by_id(comic_id)

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> ComicResponseDTO:
        await self._comic_gateway.update_base(comic_id, dto)
        translation = await self._translation_gateway.update_original(comic_id, dto.original)
        await self._translation_image_gateway.link(translation.id, dto.image_ids)
        await self._transaction.commit()

        return await self._comic_gateway.get_by_id(comic_id)

    async def delete(self, comic_id: ComicID) -> None:
        await self._comic_gateway.delete(comic_id)
        await self._transaction.commit()

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self._comic_gateway.get_by_id(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self._comic_gateway.get_by_issue_number(number)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self._comic_gateway.get_by_slug(slug)

    async def get_latest_issue_number(self) -> IssueNumber:
        return (
            await self._comic_gateway.get_list(
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
        total, comic_resp_dtos = await self._comic_gateway.get_list(query_params)

        return total, comic_resp_dtos
