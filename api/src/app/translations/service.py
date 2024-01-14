from src.app.comics.types import ComicID
from src.core.database import DatabaseHolder

from .dtos.request import TranslationRequestDTO
from .dtos.response import TranslationResponseDTO
from .types import TranslationID


class TranslationService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def create(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.create(comic_id, dto)
            await self._db_holder.commit()
        return translation_resp_dto

    async def update(
        self,
        comic_id: ComicID,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.update(
                comic_id, translation_id, dto,
            )
            await self._db_holder.commit()
        return translation_resp_dto
