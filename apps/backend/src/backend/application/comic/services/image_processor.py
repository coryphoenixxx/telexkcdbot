from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Self
from uuid import uuid4

from backend.application.comic.interfaces import (
    TranslationImagePathData,
    TranslationImageProcessorInterface,
)
from backend.application.common.interfaces import (
    ImageFileManagerInterface,
    PostProcessImageMessage,
    PublisherRouterInterface,
    TempFileManagerInterface,
)
from backend.application.image.exceptions import ImageAlreadyHasOwnerError, ImageNotFoundError
from backend.application.image.interfaces import ImageRepoInterface
from backend.domain.entities import ImageEntity, ImageLinkType, TranslationStatus
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
class TranslationImageProcessor(TranslationImageProcessorInterface):
    image_repo: ImageRepoInterface
    temp_file_manager: TempFileManagerInterface
    image_file_manager: ImageFileManagerInterface
    publisher: PublisherRouterInterface

    def __post_init__(self) -> None:
        self.created_image_ids: list[ImageId] = []

    async def create_new(
        self,
        translation_id: TranslationId,
        image_ids: list[ImageId],
        path_data: TranslationImagePathData,
    ) -> None:
        image_ids = deduplicate(image_ids)
        images = await self.image_repo.load_many(image_ids)

        for index, image in enumerate(images):
            await self._create_image(translation_id, image, path_data)
            image.position_number = index

        await self.image_repo.update_many(images)

    async def delete_linked(self, translation_id: TranslationId) -> None:
        linked_image_ids = await self._get_linked_images_ids(translation_id)
        to_delete_images = await self.image_repo.load_many(linked_image_ids)

        for image in to_delete_images:
            image.is_deleted = True

        await self.image_repo.update_many(to_delete_images)

    async def update_state(
        self,
        translation_id: TranslationId,
        image_ids: list[ImageId],
        path_data: TranslationImagePathData,
    ) -> None:
        image_ids = deduplicate(image_ids)
        linked_image_ids = await self._get_linked_images_ids(translation_id)
        image_ids_set, linked_image_ids_set = set(image_ids), set(linked_image_ids)

        to_create_image_ids_set = image_ids_set - linked_image_ids_set
        to_delete_image_ids_set = linked_image_ids_set - image_ids_set
        to_update_image_ids_set = image_ids_set & linked_image_ids_set

        all_images = await self.image_repo.load_many(image_ids_set | linked_image_ids_set)

        for image in all_images:
            if image.id in image_ids:
                image.position_number = image_ids.index(image.id)
            if image.id in to_create_image_ids_set:
                await self._create_image(translation_id, image, path_data)
            if image.id in to_delete_image_ids_set:
                image.is_deleted = True
            if image.id in to_update_image_ids_set:
                await self._move_image_files(image, path_data)

        await self.image_repo.update_many(all_images)

    async def publish_created(self) -> None:
        for image_id in self.created_image_ids:
            await self.publisher.publish(PostProcessImageMessage(image_id=image_id.value))

    async def _create_image(
        self,
        translation_id: TranslationId,
        image: ImageEntity,
        path_data: TranslationImagePathData,
    ) -> None:
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
            original_slug=path_data.original_title.slug,
            translation_slug=path_data.translation_title.slug,
            status=path_data.status,
            dimensions=image_file.dimensions,
            fmt=image_file.format,
        ).build()

        image.create(
            link_type=ImageLinkType.TRANSLATION,
            link_id=translation_id,
            original_path=original_path,
        )

        await self.image_file_manager.persist(image_file, original_path)

        self.created_image_ids.append(image.id)

    async def _get_linked_images_ids(self, translation_id: TranslationId) -> Iterable[ImageId]:
        return await self.image_repo.get_linked_image_ids(ImageLinkType.TRANSLATION, translation_id)

    async def _move_image_files(
        self,
        image: ImageEntity,
        path_data: TranslationImagePathData,
    ) -> None:
        for path_attr_name in ("original_path", "converted_path", "x2_path"):
            old_path: Path | None = getattr(image, path_attr_name)
            if old_path is None:
                continue

            old_path_obj = TranslationImagePathBuilder.from_path(old_path)

            old_path_obj.number = path_data.number
            old_path_obj.original_slug = path_data.original_title.slug
            old_path_obj.translation_slug = path_data.translation_title.slug
            old_path_obj.language = path_data.language
            old_path_obj.status = path_data.status

            new_path = old_path_obj.build()

            setattr(image, path_attr_name, new_path)

            await self.image_file_manager.move(old_path, new_path)


def deduplicate(lst: list[Any]) -> list[Any]:
    seen = set()
    result = []

    for i in lst:
        if i not in seen:
            result.append(i)
            seen.add(i)

    return result
