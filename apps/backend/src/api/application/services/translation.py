from api.application.dtos.common import Language
from api.application.dtos.requests import TranslationRequestDTO
from api.application.dtos.responses import TranslationResponseDTO
from api.core.exceptions import (
    OriginalTranslationOperationForbiddenError,
)
from api.core.value_objects import ComicID, TranslationID
from api.infrastructure.database.repositories import (
    ComicRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from api.infrastructure.database.transaction import TransactionManager


class TranslationService:
    def __init__(
        self,
        transaction: TransactionManager,
        translation_repo: TranslationRepo,
        comic_repo: ComicRepo,
        translation_image_repo: TranslationImageRepo,
    ) -> None:
        self._transaction = transaction
        self._comic_repo = comic_repo
        self._translation_repo = translation_repo
        self._translation_image_repo = translation_image_repo

    async def add(self, comic_id: ComicID, dto: TranslationRequestDTO) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self._translation_repo.create(comic_id, dto)
        await self._translation_image_repo.attach_image(translation.id, dto.image_ids)

        await self._transaction.commit()

        return await self._translation_repo.get_by_id(translation.id)

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        candidate = await self._translation_repo.get_by_id(translation_id)

        if candidate.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self._translation_repo.update(translation_id, dto)

        await self._transaction.commit()

        return await self._translation_repo.get_by_id(translation_id)

    async def delete(self, translation_id: TranslationID) -> None:
        translation = await self._translation_repo.get_by_id(
            translation_id
        )  # TODO: нужен отдельный check, is_original

        if translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self._translation_repo.delete(translation_id)
        await self._transaction.commit()

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return await self._translation_repo.get_by_id(translation_id)

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO:
        return await self._translation_repo.get_by_language(comic_id, language)

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        return await self._comic_repo.get_translations(comic_id)

    async def get_translation_drafts(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        return await self._comic_repo.get_translation_drafts(comic_id)

    async def publish(self, translation_id: TranslationID) -> None:
        candidate = await self._translation_repo.get_by_id(translation_id)

        if candidate.is_draft:
            published_translations = await self._comic_repo.get_translations(
                comic_id=candidate.comic_id,
            )

            published = None
            for tr in published_translations:
                if tr.language == candidate.language:
                    published = await self._translation_repo.get_by_id(tr.id)
                    break

            if published:
                await self._translation_repo.update_draft_status(
                    published.id,
                    new_draft_status=True,
                )

            await self._translation_repo.update_draft_status(
                candidate.id,
                new_draft_status=False,
            )

            await self._transaction.commit()
