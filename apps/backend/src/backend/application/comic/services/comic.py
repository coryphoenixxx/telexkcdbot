from dataclasses import dataclass

from backend.application.comic.dtos import (
    ComicRequestDTO,
    ComicResponseDTO,
    TranslationImageRequestDTO,
    TranslationImageResponseDTO,
    TranslationRequestDTO,
    TranslationResponseDTO,
)
from backend.application.comic.exceptions import (
    OriginalTranslationOperationForbiddenError,
    TranslationIsAlreadyPublishedError,
    TranslationNotFoundError,
)
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TagRepoInterface,
    TranslationImageRepoInterface,
    TranslationRepoInterface,
)
from backend.application.common.interfaces import (
    ConvertImageMessage,
    PublisherRouterInterface,
    TransactionManagerInterface,
    TranslationImageFileManagerInterface,
)
from backend.application.common.pagination import ComicFilterParams, Limit, Order, TotalCount
from backend.core.value_objects import ComicID, IssueNumber, Language, TranslationID


@dataclass(slots=True)
class ComicWriteService:
    transaction: TransactionManagerInterface
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    translation_image_repo: TranslationImageRepoInterface
    tag_repo: TagRepoInterface
    image_file_manager: TranslationImageFileManagerInterface
    publisher: PublisherRouterInterface

    async def create(self, dto: ComicRequestDTO) -> ComicResponseDTO:
        comic_id = await self.comic_repo.create(dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        translation = await self.translation_repo.create(comic_id, dto.original)
        image_dto = await self._create_image(translation.id, dto.number, dto.original)

        await self.transaction.commit()

        await self._convert(image_dto)

        return await self.comic_repo.get_by(comic_id)

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> ComicResponseDTO:
        await self.comic_repo.update(comic_id, dto)
        await self.tag_repo.create_many(comic_id, dto.tags)
        translation = await self.translation_repo.update_original(comic_id, dto.original)
        image_dto = await self._create_image(translation.id, dto.number, dto.original)

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
        image_dto = await self._create_image(translation.id, number, dto)

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
        image_dto = await self._create_image(translation.id, number, dto)

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
        translation_id: TranslationID,
        number: IssueNumber | None,
        dto: TranslationRequestDTO,
    ) -> TranslationImageResponseDTO | None:
        image_dto = None

        if dto.temp_image_id:
            image_rel_path = await self.image_file_manager.persist(
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
            await self.publisher.publish(ConvertImageMessage(image_id=image_dto.id.value))


@dataclass(slots=True)
class ComicDeleteService:
    transaction: TransactionManagerInterface
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface

    async def delete(self, comic_id: ComicID) -> None:
        await self.comic_repo.delete(comic_id)
        await self.transaction.commit()

    async def delete_translation(self, translation_id: TranslationID) -> None:
        translation = await self.translation_repo.get_by_id(translation_id)

        if translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self.translation_repo.delete(translation_id)
        await self.transaction.commit()


@dataclass(slots=True)
class ComicReadService:
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self.comic_repo.get_by(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self.comic_repo.get_by(number)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self.comic_repo.get_by(slug)

    async def get_latest_issue_number(self) -> IssueNumber | None:
        _, comics = await self.comic_repo.get_list(
            filter_params=ComicFilterParams(
                limit=Limit(1),
                order=Order.DESC,
            )
        )

        if comics:
            return comics[0].number
        return None

    async def get_list(
        self,
        query_params: ComicFilterParams,
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
