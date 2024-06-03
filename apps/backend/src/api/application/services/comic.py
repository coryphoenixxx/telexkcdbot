from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.infrastructure.database import ComicGateway, UnitOfWork
from api.infrastructure.database.my_types import ComicFilterParams
from api.my_types import ComicID, IssueNumber, TotalCount


class ComicService:
    def __init__(self, uow: UnitOfWork, gateway: ComicGateway):
        self._uow = uow
        self._gateway = gateway

    async def create(self, comic_req_dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_resp_dto = await self._gateway.create(comic_req_dto)

        await self._uow.commit()

        return comic_resp_dto

    async def update(self, comic_id: ComicID, comic_req_dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_resp_dto = await self._gateway.update(comic_id, comic_req_dto)
        await self._uow.commit()

        return comic_resp_dto

    async def delete(self, comic_id: ComicID) -> None:
        await self._gateway.delete(comic_id)

        await self._uow.commit()

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWTranslationsDTO:
        comic_resp_dto = await self._gateway.get_by_id(comic_id)

        return comic_resp_dto

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseWTranslationsDTO:
        comic_resp_dto = await self._gateway.get_by_issue_number(number)

        return comic_resp_dto

    async def get_by_slug(self, slug: str) -> ComicResponseWTranslationsDTO:
        comic_resp_dto = await self._gateway.get_by_slug(slug)

        return comic_resp_dto

    async def get_list(
        self,
        query_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseWTranslationsDTO]]:
        total, comic_resp_dtos = await self._gateway.get_list(query_params)

        return total, comic_resp_dtos
