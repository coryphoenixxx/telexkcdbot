from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.responses import TranslationResponseDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.infrastructure.database.holder import DatabaseHolder
from api.infrastructure.database.types import ComicFilterParams
from api.types import ComicID, IssueNumber, TotalCount


class ComicService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def create(self, comic_req_dto: ComicRequestDTO) -> ComicResponseDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.create(comic_req_dto)

            await self._db_holder.commit()

        return comic_resp_dto

    async def update(self, comic_id: ComicID, comic_req_dto: ComicRequestDTO) -> ComicResponseDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.update(comic_id, comic_req_dto)
            await self._db_holder.commit()

        return comic_resp_dto

    async def delete(self, comic_id: ComicID) -> None:
        async with self._db_holder:
            await self._db_holder.comic_repo.delete(comic_id)

            await self._db_holder.commit()

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_id(comic_id)

        return comic_resp_dto

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseWTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_issue_number(number)

        return comic_resp_dto

    async def get_by_slug(self, slug: str) -> ComicResponseWTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_slug(slug)

        return comic_resp_dto

    async def get_list(
        self,
        query_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseWTranslationsDTO]]:
        async with self._db_holder:
            total, comic_resp_dtos = await self._db_holder.comic_repo.get_list(query_params)

        return total, comic_resp_dtos

    async def get_translations(
        self,
        comic_id: ComicID,
        is_draft: bool = False,
    ) -> list[TranslationResponseDTO]:
        async with self._db_holder:
            draft_resp_dtos = await self._db_holder.comic_repo.get_translations(comic_id, is_draft)

        return draft_resp_dtos
