from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.translation import (
    OriginalTranslationOperationForbiddenError,
)
from api.infrastructure.database.holder import DatabaseHolder
from api.types import ComicID, Language, TranslationID


class TranslationService:
    def __init__(self, db_holder: DatabaseHolder):
        self._db_holder = db_holder

    async def add(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        async with self._db_holder:
            translation = await self._db_holder.translation_repo.add(comic_id, dto)
            await self._db_holder.commit()

        return translation

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        async with self._db_holder:
            candidate = await self._db_holder.translation_repo.get_by_id(translation_id)

            if candidate.language == Language.EN:
                raise OriginalTranslationOperationForbiddenError

            translation = await self._db_holder.translation_repo.update(
                translation_id=translation_id,
                dto=dto,
            )

            await self._db_holder.commit()

        return translation

    async def delete(self, translation_id: TranslationID) -> None:
        async with self._db_holder:
            tranlation = await self._db_holder.translation_repo.get_by_id(translation_id)

            if tranlation.language == Language.EN:
                raise OriginalTranslationOperationForbiddenError

            await self._db_holder.translation_repo.delete(translation_id)

            await self._db_holder.commit()

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        async with self._db_holder:
            translation = await self._db_holder.translation_repo.get_by_id(translation_id)

        return translation

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO:
        async with self._db_holder:
            translation = await self._db_holder.translation_repo.get_by_language(
                comic_id=comic_id,
                language=language,
            )

        return translation

    async def publish(self, translation_id: TranslationID):
        async with self._db_holder:
            candidate = await self._db_holder.translation_repo.get_by_id(translation_id)

            if candidate.is_draft:
                published_translations = await self._db_holder.comic_repo.get_translations(
                    comic_id=candidate.comic_id,
                )

                published = None
                for tr in published_translations:
                    if tr.language == candidate.language:
                        published = await self._db_holder.translation_repo.get_by_id(tr.id)
                        break

                if published:
                    await self._db_holder.translation_repo.update_draft_status(published.id, True)

                await self._db_holder.translation_repo.update_draft_status(candidate.id, False)

                await self._db_holder.commit()
