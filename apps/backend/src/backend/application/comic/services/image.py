from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self
from uuid import uuid4

from backend.application.comic.interfaces import (
    TranslationImagePathData,
    TranslationImageSaveHelperInterface,
)
from backend.application.common.interfaces import (
    ImageFileManagerInterface,
    TempFileManagerInterface,
)
from backend.application.image.exceptions import ImageAlreadyHasOwnerError, ImageNotFoundError
from backend.application.image.interfaces import ImageRepoInterface
from backend.domain.entities import ImageLinkType, TranslationStatus
from backend.domain.value_objects import (
    ImageId,
    IssueNumber,
    Language,
    TranslationId,
)
from backend.domain.value_objects.image_file import ImageFileObj, ImageFormat


@dataclass(slots=True, kw_only=True)
class TranslationImagePathBuilder:
    _ROOT: ClassVar[str] = "images/comics/"

    number: IssueNumber | None
    language: Language
    original_slug: str
    translation_slug: str
    random_part: str = field(default_factory=lambda: uuid4().hex[:12])
    status: TranslationStatus | None
    dimensions: tuple[int, int]
    mark: str = ""
    fmt: ImageFormat

    @classmethod
    def from_path(cls, path: Path) -> Self:
        try:
            parent_dir_path, filename = str(path.parent), path.name
            name, fmt = filename.rsplit(".", 1)
            translation_slug, random_part, dimensions_raw, *mark = name.split("_")
            w_str, h_str = dimensions_raw.split("x")

            is_published = "drafts" not in parent_dir_path
            is_extra = "extras" in parent_dir_path

            parent_dir_path = parent_dir_path.replace(cls._ROOT, "")
            dir_parts = parent_dir_path.split("/")

            if is_extra:
                if is_published:
                    _, original_slug, lang_str = dir_parts
                else:
                    _, original_slug, lang_str, _ = dir_parts
                number = None
            else:
                original_slug = translation_slug
                number_str, lang_str = dir_parts[:2]
                number = IssueNumber(int(number_str))

            language = Language(lang_str)

        except (ValueError, IndexError) as err:
            raise ValueError(f"Path `{path}` has an invalid format: {err}") from None
        return cls(
            number=number,
            language=language,
            original_slug=original_slug,
            translation_slug=translation_slug,
            random_part=random_part,
            status=TranslationStatus.PUBLISHED if is_published else None,
            dimensions=(int(w_str), int(h_str)),
            mark=f"_{mark[0]}" if mark else "",
            fmt=ImageFormat(fmt),
        )

    def build(self) -> Path:
        number = self.number.value if self.number else None
        w, h = self.dimensions

        if number and self.status == TranslationStatus.PUBLISHED:
            path_part = f"{number:05d}/{self.language}/"
        elif number:
            path_part = f"{number:05d}/{self.language}/drafts/"
        elif number is None and self.status == TranslationStatus.PUBLISHED:
            path_part = f"extras/{self.original_slug}/{self.language}/"
        else:
            path_part = f"extras/{self.original_slug}/{self.language}/drafts/"

        filename = f"{self.translation_slug}_{self.random_part}_{w}x{h}{self.mark}.{self.fmt}"

        return Path(self._ROOT) / path_part / filename


@dataclass(slots=True)
class TranslationImageSaveHelper(TranslationImageSaveHelperInterface):
    image_repo: ImageRepoInterface
    temp_file_manager: TempFileManagerInterface
    image_file_manager: ImageFileManagerInterface

    async def update_image(
        self,
        translation_id: TranslationId,
        old_image_id: ImageId | None,
        new_image_id: ImageId | None,
        path_data: TranslationImagePathData,
        move_image_required: bool,
    ) -> ImageId | None:
        created_image_id = None

        if old_image_id is None and new_image_id:
            await self.create_new_image(translation_id, new_image_id, path_data)
            created_image_id = new_image_id

        elif old_image_id and new_image_id is None:
            await self.soft_delete_image(old_image_id)

        elif old_image_id and old_image_id == new_image_id:
            if move_image_required:
                await self.move_image(old_image_id, path_data)

        elif new_image_id and old_image_id != new_image_id:
            await self.create_new_image(translation_id, new_image_id, path_data)
            created_image_id = new_image_id
            await self.soft_delete_image(old_image_id)

        return created_image_id

    async def create_new_image(
        self,
        translation_id: TranslationId,
        image_id: ImageId,
        path_data: TranslationImagePathData,
    ) -> None:
        image = await self.image_repo.load(image_id)

        if image.is_deleted:
            raise ImageNotFoundError(image.id)

        if image.has_another_owner(ImageLinkType.TRANSLATION, translation_id):
            raise ImageAlreadyHasOwnerError(image.id)

        image_file = ImageFileObj(
            source=self.temp_file_manager.get_abs_path(
                temp_file_id=image.temp_image_id,  # type: ignore[arg-type]
            )
        )

        original_path = TranslationImagePathBuilder(
            number=path_data.number,
            language=path_data.language,
            original_slug=path_data.original_title_slug,
            translation_slug=path_data.translation_title_slug,
            status=path_data.status,
            dimensions=image_file.dimensions,
            fmt=image_file.format,
        ).build()

        image.create(
            entity_type=ImageLinkType.TRANSLATION,
            entity_id=translation_id,
            original_path=original_path,
        )

        await self.image_file_manager.save(image_file, original_path)

        await self.image_repo.update(image)

    async def move_image(
        self,
        image_id: ImageId,
        new_path_data: TranslationImagePathData,
    ) -> None:
        image = await self.image_repo.load(image_id)

        if image.image_path:
            old_path: Path = image.image_path

            old_path_obj = TranslationImagePathBuilder.from_path(old_path)

            old_path_obj.number = new_path_data.number
            old_path_obj.original_slug = new_path_data.original_title_slug
            old_path_obj.translation_slug = new_path_data.translation_title_slug
            old_path_obj.language = new_path_data.language
            old_path_obj.status = new_path_data.status

            new_path = old_path_obj.build()

            image.image_path = new_path

            await self.image_file_manager.move(old_path, new_path)

            await self.image_repo.update(image)

    async def soft_delete_image(self, image_id: ImageId | None) -> None:
        if image_id:
            image = await self.image_repo.load(image_id)
            image.is_deleted = True
            await self.image_repo.update(image)

    async def get_linked_image_id(self, translation_id: TranslationId) -> ImageId | None:
        return await self.image_repo.get_linked_image_id(
            link_type=ImageLinkType.TRANSLATION,
            link_id=translation_id,
        )
