from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self
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
from backend.domain.entities import ImageLinkType, TranslationStatus
from backend.domain.value_objects import (
    ImageId,
    IssueNumber,
    Language,
    PositiveInt,
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

    async def create_many(
        self,
        link_id: PositiveInt,
        image_ids: Iterable[ImageId],
        path_data: TranslationImagePathData,
    ) -> None:
        for image_id in image_ids:
            image = await self.image_repo.load(image_id)

            if image.is_deleted:
                raise ImageNotFoundError(image.id)

            if image.has_another_owner(ImageLinkType.TRANSLATION, link_id):
                raise ImageAlreadyHasOwnerError(image_id)

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

            image.create(ImageLinkType.TRANSLATION, link_id, original_path)

            await self.image_repo.update(image)

            await self.image_file_manager.persist(image_file, original_path)

    async def update_many(
        self,
        link_id: PositiveInt,
        image_ids: Iterable[ImageId],
        path_data: TranslationImagePathData,
    ) -> list[ImageId]:
        (
            to_create_image_ids,
            to_delete_image_ids,
            to_move_images_image_ids,
        ) = await self._separate(link_id, image_ids)

        await self.create_many(link_id, to_create_image_ids, path_data)
        await self.delete_many(to_delete_image_ids)
        await self._move_images(to_move_images_image_ids, path_data)

        return list(to_create_image_ids)

    async def delete_many(self, image_ids: Iterable[ImageId]) -> None:
        for image_id in image_ids:
            image = await self.image_repo.load(image_id)
            image.mark_deleted()
            await self.image_repo.update(image)

    async def postprocess_in_background(self, image_ids: Iterable[ImageId]) -> None:
        for image_id in image_ids:
            await self.publisher.publish(PostProcessImageMessage(image_id=image_id.value))

    async def _move_images(
        self,
        image_ids: Iterable[ImageId],
        path_data: TranslationImagePathData,
    ) -> None:
        for image_id in image_ids:
            image = await self.image_repo.load(image_id)

            for path_attr_name in (
                "original_path",
                "converted_path",
                "converted_2x_path",
            ):
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
            await self.image_repo.update(image)

    async def _separate(
        self,
        link_id: PositiveInt,
        image_ids: Iterable[ImageId],
    ) -> tuple[
        Sequence[ImageId],
        Sequence[ImageId],
        Sequence[ImageId],
    ]:
        linked_image_ids = await self.image_repo.get_linked_image_ids(
            link_type=ImageLinkType.TRANSLATION,
            link_id=link_id,
        )
        image_ids_set, linked_image_ids_set = set(image_ids), set(linked_image_ids)

        to_create_image_ids = list(image_ids_set - linked_image_ids_set)
        to_delete_image_ids = list(linked_image_ids_set - image_ids_set)
        to_move_images_image_ids = list(set(image_ids) - set(to_create_image_ids))

        return to_create_image_ids, to_delete_image_ids, to_move_images_image_ids
