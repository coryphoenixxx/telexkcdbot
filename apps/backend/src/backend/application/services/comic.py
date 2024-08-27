from dataclasses import dataclass

from backend.application.dtos import (
    ComicRequestDTO,
    ComicResponseDTO,
    TranslationImageRequestDTO,
    TranslationImageResponseDTO,
    TranslationRequestDTO,
    TranslationResponseDTO,
)
from backend.core.exceptions.base import BaseAppError
from backend.core.value_objects import ComicID, IssueNumber, Language, TranslationID
from backend.infrastructure.broker.messages import ConvertImageMessage
from backend.infrastructure.broker.publisher_contrainer import PublisherContainer
from backend.infrastructure.database.dtos import ComicFilterParams, Limit, Order, TotalCount
from backend.infrastructure.database.repositories import (
    ComicRepo,
    TagRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from backend.infrastructure.database.repositories.translation import TranslationNotFoundError
from backend.infrastructure.database.transaction import TransactionManager
from backend.infrastructure.filesystem import TranslationImageFileManager


@dataclass(slots=True, eq=False)
class OriginalTranslationOperationForbiddenError(BaseAppError):
    @property
    def message(self) -> str:
        return "Operations on English translation are forbidden."


@dataclass(slots=True, eq=False)
class TranslationIsAlreadyPublishedError(BaseAppError):
    @property
    def message(self) -> str:
        return "The translation has already been published."


@dataclass(slots=True, eq=False, frozen=True)
class ComicWriteService:
    transaction: TransactionManager
    comic_repo: ComicRepo
    translation_repo: TranslationRepo
    translation_image_repo: TranslationImageRepo
    tag_repo: TagRepo
    image_file_manager: TranslationImageFileManager
    publisher: PublisherContainer

    async def create(self, dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_id = await self.comic_repo.create_base(dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        translation = await self.translation_repo.create(comic_id, dto.original)
        image_dto = await self._create_image(dto.number, dto.original, translation.id)

        await self.transaction.commit()

        await self._convert(image_dto)

        return await self.comic_repo.get_by(comic_id)

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> ComicResponseDTO:
        await self.comic_repo.update_base(comic_id, dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        translation = await self.translation_repo.update_original(comic_id, dto.original)
        image_dto = await self._create_image(dto.number, dto.original, translation.id)

        await self.transaction.commit()

        await self._convert(image_dto)

        return await self.comic_repo.get_by(comic_id)

    async def add_translation(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self.translation_repo.create(comic_id, dto)
        number = await self.comic_repo.get_issue_number_by_id(comic_id)
        image_dto = await self._create_image(number, dto, translation.id)

        await self.transaction.commit()

        await self._convert(image_dto)

        return await self.translation_repo.get_by_id(translation.id)

    async def update_translation(
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
        image_dto = await self._create_image(number, dto, translation.id)

        await self.transaction.commit()

        await self._convert(image_dto)

        return await self.translation_repo.get_by_id(translation.id)

    async def publish_translation_draft(self, translation_id: TranslationID) -> None:
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

    async def _create_image(
        self,
        number: IssueNumber,
        dto: TranslationRequestDTO,
        translation_id: TranslationID,
    ) -> TranslationImageResponseDTO | None:
        image_dto = None

        if dto.temp_image_id:
            image_rel_path = await self.image_file_manager.save(
                temp_image_id=dto.temp_image_id,
                number=number,
                title=dto.title,
                language=dto.language,
                is_draft=dto.is_draft,
            )

            image_dto = await self.translation_image_repo.create(
                dto=TranslationImageRequestDTO(
                    translation_id=translation_id,
                    original=image_rel_path,
                )
            )

        return image_dto

    async def _convert(self, image_dto: TranslationImageResponseDTO | None) -> None:
        if image_dto:
            await self.publisher.publish(ConvertImageMessage(image_id=image_dto.id))


@dataclass(slots=True, eq=False, frozen=True)
class ComicDeleteService:
    transaction: TransactionManager
    comic_repo: ComicRepo
    translation_repo: TranslationRepo

    async def delete(self, comic_id: ComicID) -> None:
        await self.comic_repo.delete(comic_id)
        await self.transaction.commit()

    async def delete_translation(self, translation_id: TranslationID) -> None:
        translation = await self.translation_repo.get_by_id(translation_id)

        if translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self.translation_repo.delete(translation_id)
        await self.transaction.commit()


@dataclass(slots=True, eq=False, frozen=True)
class ComicReadService:
    comic_repo: ComicRepo
    translation_repo: TranslationRepo

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self.comic_repo.get_by(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self.comic_repo.get_by(number)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self.comic_repo.get_by(slug)

    async def get_latest_issue_number(self) -> IssueNumber:
        return (
            await self.comic_repo.get_list(
                filter_params=ComicFilterParams(
                    limit=Limit(1),
                    order=Order.DESC,
                )
            )
        )[1][0].number

    async def get_list(
        self,
        query_params: ComicFilterParams = ComicFilterParams(),
    ) -> tuple[TotalCount, list[ComicResponseDTO]]:
        return await self.comic_repo.get_list(query_params)

    async def get_translation_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return await self.translation_repo.get_by_id(translation_id)

    async def get_translation_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO:
        translation = await self.translation_repo.get_by_language(comic_id, language)
        if not translation:
            raise TranslationNotFoundError(language)
        return translation

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        return await self.comic_repo.get_translations(comic_id)
