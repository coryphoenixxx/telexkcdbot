from dataclasses import dataclass

from backend.application.comic.dtos import (
    TranslationImageRequestDTO,
    TranslationImageResponseDTO,
    TranslationRequestDTO,
)
from backend.application.comic.interfaces import TranslationImageRepoInterface
from backend.application.common.interfaces import (
    ConvertImageMessage,
    PublisherRouterInterface,
    TranslationImageFileManagerInterface,
)
from backend.core.value_objects import IssueNumber, TranslationID


@dataclass(slots=True)
class ProcessImageMixin:
    translation_image_repo: TranslationImageRepoInterface
    image_file_manager: TranslationImageFileManagerInterface
    publisher: PublisherRouterInterface

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
