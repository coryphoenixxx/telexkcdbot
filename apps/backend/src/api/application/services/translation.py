from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.translation import EnglishTranslationOperationForbiddenError
from api.application.types import ComicID, Language, TranslationID
from api.infrastructure.database.holder import DatabaseHolder


class TranslationService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def add(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.add(comic_id, dto)
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

            if translation_resp_dto.language == Language.EN:
                raise EnglishTranslationOperationForbiddenError

            await self._db_holder.commit()

        return translation_resp_dto

    async def delete(self, translation_id: TranslationID) -> None:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.get_by_id(translation_id)
            if translation_resp_dto.language == Language.EN:
                raise EnglishTranslationOperationForbiddenError

            await self._db_holder.translation_repo.delete(translation_id)
            await self._db_holder.commit()

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        async with self._db_holder:
            translation_resp_dto = await self._db_holder.translation_repo.get_by_id(translation_id)

        return translation_resp_dto
