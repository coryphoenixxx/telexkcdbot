from src.app.translations.dtos import TranslationRequestDTO
from src.core.database import DatabaseHolder

from .dtos.requests import ComicRequestDTO
from .dtos.responses import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .types import ComicID


class ComicService:
    def __init__(self, holder: DatabaseHolder):
        self._holder = holder

    async def create(
        self,
        comic_req_dto: ComicRequestDTO,
        en_translation_req_dto: TranslationRequestDTO,
    ) -> ComicResponseWithTranslationsDTO:
        async with self._holder:
            comic_resp_dto = await self._holder.comic_repo.create(
                dto=comic_req_dto,
                en_title=en_translation_req_dto.title,
            )
            translation_resp_dto = await self._holder.translation_repo.create(
                comic_id=comic_resp_dto.id,
                dto=en_translation_req_dto,
            )
            comic_resp_dto.translations.append(translation_resp_dto)
            await self._holder.commit()

            return comic_resp_dto

    async def update(
        self,
        comic_id: ComicID,
        comic_req_dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        async with self._holder:
            comic_resp_dto = await self._holder.comic_repo.update(comic_id, comic_req_dto)
            await self._holder.commit()

            return comic_resp_dto

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWithTranslationsDTO:
        async with self._holder:
            comic_resp_dto = await self._holder.comic_repo.get_by_id_with_translations(comic_id)

            return comic_resp_dto

    async def get_by_issue_number(self, issue_number: int) -> ComicResponseWithTranslationsDTO:
        async with self._holder:
            comic_resp_dto = await self._holder.comic_repo.get_by_issue_number(issue_number)

            return comic_resp_dto

    async def get_by_slug(self, slug: str) -> ComicResponseWithTranslationsDTO:
        async with self._holder:
            comic_resp_dto = await self._holder.comic_repo.get_by_slug(slug)

            return comic_resp_dto

    async def get_all(self) -> list[ComicResponseWithTranslationsDTO]:
        async with self._holder:
            comic_resp_dtos = await self._holder.comic_repo.get_all()

            return comic_resp_dtos
