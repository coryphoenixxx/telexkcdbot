from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Self
from uuid import uuid4

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
    TranslationTitle,
)
from backend.domain.value_objects.image_file import ImageFileObj, ImageFormat


@dataclass(slots=True)
class TranslationImagePathData:
    number: IssueNumber | None
    title: TranslationTitle
    language: Language
    status: TranslationStatus


@dataclass(slots=True)
class TranslationImageFilename:
    slug: str
    dimensions: tuple[int, int]
    fmt: ImageFormat
    mark: str = ""
    random_part: str | None = None

    def __post_init__(self) -> None:
        if self.random_part is None:
            self.random_part = uuid4().hex[:12]

    @classmethod
    def build(cls, filename: str) -> Self:
        try:
            name, fmt = filename.rsplit(".", 1)
            slug, random_part, dimensions_raw, *mark = name.split("_")
            w, h = dimensions_raw.split("x")
            dimensions = (int(w), int(h))
        except ValueError:
            raise ValueError(f"Filename `{filename}` has an invalid format.") from None
        return cls(
            slug=slug,
            random_part=random_part,
            dimensions=dimensions,
            mark=f"_{mark[0]}" if mark else "",
            fmt=ImageFormat(fmt),
        )

    def generate(self) -> str:
        return (
            f"{self.slug}_{self.random_part}_"
            f"{self.dimensions[0]}x{self.dimensions[1]}{self.mark}.{self.fmt}"
        )


@dataclass(slots=True)
class RelativeImagePathBuilder:
    path_data: TranslationImagePathData
    dimensions: tuple[int, int] | None = None
    fmt: ImageFormat | None = None

    @property
    def parent_dir(self) -> Path:
        number = self.path_data.number.value if self.path_data.number else None
        status = self.path_data.status

        if number is None and status == TranslationStatus.PUBLISHED:
            part = f"extras/{self.path_data.title.slug}/{self.path_data.language}/"
        elif number is None and status != TranslationStatus.PUBLISHED:
            part = f"extras/{self.path_data.title.slug}/{self.path_data.language}/drafts/"
        elif number and status == TranslationStatus.PUBLISHED:
            part = f"{number:05d}/{self.path_data.language}/"
        elif number and status != TranslationStatus.PUBLISHED:
            part = f"{number:05d}/{self.path_data.language}/drafts/"
        else:
            raise ValueError(f"Invalid translation image path data ({self.path_data})")

        return Path("images/comics/") / part

    @property
    def filename(self) -> str:
        if self.dimensions is None or self.fmt is None:
            raise ValueError("Can't build filename without dimensions or format.")
        return TranslationImageFilename(
            slug=self.path_data.title.slug,
            dimensions=self.dimensions,
            fmt=self.fmt,
        ).generate()

    @property
    def full_path(self) -> Path:
        return self.parent_dir / self.filename


@dataclass(slots=True)
class ProcessTranslationImageMixin:
    image_repo: ImageRepoInterface
    temp_file_manager: TempFileManagerInterface
    image_file_manager: ImageFileManagerInterface
    publisher: PublisherRouterInterface

    async def create_images(
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
                    image.temp_image_id,  # type: ignore[arg-type]
                )
            )

            original_path = RelativeImagePathBuilder(
                path_data=path_data,
                dimensions=image_file.dimensions,
                fmt=image_file.format,
            ).full_path

            image.create(ImageLinkType.TRANSLATION, link_id, original_path)

            await self.image_repo.update(image)

            await self.image_file_manager.persist(image_file, original_path)

    async def delete_images(self, image_ids: Iterable[ImageId]) -> None:
        for image_id in image_ids:
            image = await self.image_repo.load(image_id)
            image.mark_deleted()
            await self.image_repo.update(image)

    async def process_images(
        self,
        link_id: PositiveInt,
        image_ids: Iterable[ImageId],
        path_data: TranslationImagePathData,
    ) -> list[ImageId]:
        (
            to_create_image_ids,
            to_delete_image_ids,
            to_move_images_image_ids,
        ) = await self._separate_images(link_id, image_ids)

        await self.create_images(link_id, to_create_image_ids, path_data)
        await self.delete_images(to_delete_image_ids)
        await self.move_images(to_move_images_image_ids, path_data)

        return list(to_create_image_ids)

    async def postprocess_images_in_background(self, image_ids: Iterable[ImageId]) -> None:
        for image_id in image_ids:
            await self.publisher.publish(PostProcessImageMessage(image_id=image_id.value))

    async def move_images(
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
                old_path = getattr(image, path_attr_name)
                if old_path is None:
                    continue

                old_filename = TranslationImageFilename.build(old_path.name)
                old_filename.slug = path_data.title.slug
                new_filename = old_filename.generate()

                new_path = RelativeImagePathBuilder(path_data).parent_dir / new_filename

                setattr(image, path_attr_name, new_path)

                await self.image_file_manager.move(old_path, new_path)
            await self.image_repo.update(image)

    async def _separate_images(
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
