from dataclasses import dataclass

from backend.application.comic.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.comic.exceptions import (
    OriginalTranslationOperationForbiddenError,
    TranslationIsAlreadyPublishedError,
    TranslationNotFoundError,
)
from backend.application.comic.interfaces import ComicRepoInterface, TranslationRepoInterface
from backend.application.common.interfaces import TransactionManagerInterface
from backend.core.value_objects import ComicID, Language, TranslationID

from .mixins import ProcessTranslationImageMixin


@dataclass(slots=True)
class AddTranslationInteractor(ProcessTranslationImageMixin):
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    transaction: TransactionManagerInterface

    async def execute(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self.translation_repo.create(comic_id, dto)
        number = await self.comic_repo.get_issue_number_by_id(comic_id)
        image = await self.create_image(translation.id, number, dto)

        await self.transaction.commit()

        await self.process_image_in_background(
            temp_image_id=dto.temp_image_id,
            image_dto=image,
        )

        return await self.translation_repo.get_by_id(translation.id)


@dataclass(slots=True)
class FullUpdateTranslationInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        db_translation = await self.translation_repo.get_by_id(translation_id)
        if db_translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self.translation_repo.update(translation_id, dto)
        number = await self.comic_repo.get_issue_number_by_id(translation.comic_id)
        image = await self.create_image(translation.id, number, dto)

        await self.transaction.commit()

        await self.process_image_in_background(
            temp_image_id=dto.temp_image_id,
            image_dto=image,
        )

        return await self.translation_repo.get_by_id(translation.id)


@dataclass(slots=True)
class PublishTranslationDraftInteractor:
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, translation_id: TranslationID) -> None:
        # TODO: redesign
        candidate = await self.translation_repo.get_by_id(translation_id)

        if candidate.is_draft:
            if published := await self.translation_repo.get_by_language(
                comic_id=candidate.comic_id,
                language=candidate.language,
            ):
                await self.translation_repo.update_draft_status(published.id, True)
            await self.translation_repo.update_draft_status(candidate.id, False)
            await self.transaction.commit()
        else:
            raise TranslationIsAlreadyPublishedError


@dataclass(slots=True)
class DeleteTranslationDraftInteractor:
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, translation_id: TranslationID) -> None:
        translation = await self.translation_repo.get_by_id(translation_id)

        if translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self.translation_repo.delete(translation_id)
        await self.transaction.commit()


@dataclass(slots=True)
class TranslationReader:
    translation_repo: TranslationRepoInterface

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return await self.translation_repo.get_by_id(translation_id)

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO:
        translation = await self.translation_repo.get_by_language(comic_id, language)
        if not translation:
            raise TranslationNotFoundError(language)
        return translation
