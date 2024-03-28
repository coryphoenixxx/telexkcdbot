from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.types import TranslationID
from api.infrastructure.database.holder import DatabaseHolder


class TranslationService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def create(self, dto: TranslationRequestDTO) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.create(dto)
            await self._db_holder.commit()

        return translation_resp_dto

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.update(
                translation_id=translation_id,
                dto=dto,
            )
            await self._db_holder.commit()

        return translation_resp_dto

    async def delete(self, translation_id: TranslationID):
        async with self._db_holder:
            await self._db_holder.translation_repo.delete(translation_id)
            await self._db_holder.commit()
