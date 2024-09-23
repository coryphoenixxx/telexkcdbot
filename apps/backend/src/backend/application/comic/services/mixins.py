from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from backend.application.comic.dtos import (
    TranslationImageRequestDTO,
    TranslationImageResponseDTO,
    TranslationRequestDTO,
)
from backend.application.comic.interfaces import TranslationImageRepoInterface
from backend.application.common.dtos import ImageFormat, ImageObj
from backend.application.common.interfaces import (
    ImageFileManagerInterface,
    ProcessTranslationImageMessage,
    PublisherRouterInterface,
)
from backend.application.utils import slugify
from backend.core.value_objects import (
    IssueNumber,
    Language,
    TempFileID,
    TranslationID,
)
from backend.infrastructure.filesystem import TempFileManager


@dataclass(slots=True)
class ProcessTranslationImageMixin:
    translation_image_repo: TranslationImageRepoInterface
    temp_file_manager: TempFileManager
    image_file_manager: ImageFileManagerInterface
    publisher: PublisherRouterInterface

    async def create_image(
        self,
        translation_id: TranslationID,
        number: IssueNumber | None,
        translation: TranslationRequestDTO,
    ) -> TranslationImageResponseDTO | None:
        if translation.temp_image_id is None:
            return None

        image = ImageObj(self.temp_file_manager.get_abs_path_by_id(translation.temp_image_id))

        save_path = self._build_image_relative_path(
            number=number,
            title=translation.title,
            language=translation.language,
            is_draft=translation.is_draft,
            dimensions=image.dimensions,
            fmt=image.format,
        )

        dto = await self.translation_image_repo.create(
            dto=TranslationImageRequestDTO(
                translation_id=translation_id,
                original_path=save_path,
            )
        )

        await self.image_file_manager.persist(image, save_path)

        return dto

    async def process_image_in_background(
        self,
        temp_image_id: TempFileID | None,
        image_dto: TranslationImageResponseDTO | None,
    ) -> None:
        if temp_image_id and image_dto:
            await self.publisher.publish(
                ProcessTranslationImageMessage(
                    temp_image_id=temp_image_id,
                    translation_image_id=image_dto.id,
                )
            )

    def _build_image_relative_path(
        self,
        number: IssueNumber | None,
        title: str,
        language: Language,
        is_draft: bool,
        dimensions: tuple[int, int],
        fmt: ImageFormat,
    ) -> Path:
        slug = slugify(title)

        match (number, title, language, is_draft):
            case [None, _, _, False]:
                part = f"extras/{slug}/{language}/"
            case [None, _, _, True]:
                part = f"extras/{slug}/{language}/drafts/"
            case [number, _, _, False] if number is not None:
                part = f"{number.value:05d}/{language}/"
            case [number, _, _, True] if number is not None:
                part = f"{number.value:05d}/{language}/drafts/"
            case _:
                raise ValueError("Invalid translation image path data.")

        filename = f"{slug}_{uuid4().hex[:8]}_{dimensions[0]}x{dimensions[1]}.{fmt}"

        return Path("images/comics/") / part / filename
