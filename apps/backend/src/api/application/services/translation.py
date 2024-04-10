from api.application.dtos.requests.translation import (
    TranslationDraftRequestDTO,
    TranslationRequestDTO,
)
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.translation import (
    DraftForDraftCreationError,
    EnglishTranslationOperationForbiddenError,
)
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

    async def add_draft(
        self,
        original_id: TranslationID,
        dto: TranslationDraftRequestDTO,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            original_resp_dto = await self._db_holder.translation_repo.get_by_id(original_id)

            if original_resp_dto.language == Language.EN:
                raise EnglishTranslationOperationForbiddenError(
                    message="Creating drafts for English comics is forbidden.",
                )

            if original_resp_dto.is_draft:
                raise DraftForDraftCreationError(translation_id=original_id)

            dto.original_id = original_resp_dto.id
            dto.language = original_resp_dto.language

            draft_resp_dto = await self._db_holder.translation_repo.add(
                comic_id=original_resp_dto.comic_id,
                dto=dto,
            )

            await self._db_holder.commit()

        return draft_resp_dto
