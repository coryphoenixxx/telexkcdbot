from src.app.translations.dtos.request import TranslationRequestDTO
from src.core.database import DatabaseHolder

from .dtos.request import ComicRequestDTO
from .dtos.response import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .types import ComicID


class ComicService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def create(
        self,
        comic_req_dto: ComicRequestDTO,
        en_translation_req_dto: TranslationRequestDTO,
    ) -> ComicResponseWithTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.create(
                dto=comic_req_dto,
                en_title=en_translation_req_dto.title,
            )
            translation_resp_dto = await self._db_holder.translation_repo.create(
                comic_id=comic_resp_dto.id,
                dto=en_translation_req_dto,
            )
            comic_resp_dto.translations.append(translation_resp_dto)
            await self._db_holder.commit()

            return comic_resp_dto

    async def update(
        self,
        comic_id: ComicID,
        comic_req_dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.update(comic_id, comic_req_dto)
            await self._db_holder.commit()

            return comic_resp_dto

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWithTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_id_with_translations(comic_id)

            return comic_resp_dto

    async def get_by_issue_number(self, issue_number: int) -> ComicResponseWithTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_issue_number(issue_number)

            return comic_resp_dto

    async def get_by_title(self, title: str) -> ComicResponseWithTranslationsDTO:
        async with self._db_holder:
            comic_resp_dto = await self._db_holder.comic_repo.get_by_title(title)

            return comic_resp_dto

    async def get_list(self) -> list[ComicResponseWithTranslationsDTO]:
        async with self._db_holder:
            comic_resp_dtos = await self._db_holder.comic_repo.get_list()

            return comic_resp_dtos

    async def delete(self, comic_id: ComicID):
        async with self._db_holder:
            await self._db_holder.comic_repo.delete(comic_id)
            await self._db_holder.commit()
