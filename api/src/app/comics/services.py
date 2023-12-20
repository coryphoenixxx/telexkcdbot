from pathlib import Path

import magic
from fastapi import HTTPException
from PIL import Image
from starlette import status

from src.core.utils.uow import UOW

from .dtos import ComicCreateDTO, ComicGetDTO
from .image_utils.dtos import ComicImageDTO
from .image_utils.saver import ImageSaver
from .image_utils.types import ImageFormatEnum, ImageTypeEnum
from .schemas import ComicCreateSchema


def get_real_image_format(filename: Path) -> ImageFormatEnum:
    try:
        fmt = ImageFormatEnum(magic.from_file(filename=filename, mime=True).split("/")[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type. Supported: {', '.join([fmt.value for fmt in ImageFormatEnum])}",
        )
    return fmt


class ComicsService:
    def __init__(self, uow: UOW):
        self._uow = uow

    async def create_comic(
        self,
        comic_create_schema: ComicCreateSchema,
        tmp_image: Path | None,
        tmp_image_2x: Path | None,
    ) -> ComicGetDTO:
        comic_create_dto = ComicCreateDTO.from_schema(comic_create_schema)

        async with self._uow:
            issue_number = await self._generate_issue_number_if_not_exists(
                comic_create_dto.issue_number,
            )

            comic_create_dto.issue_number = comic_create_dto.translation.issue_number = issue_number

            image_dto = (
                ComicImageDTO(
                    issue_number=issue_number,
                    path=tmp_image,
                    format_=get_real_image_format(tmp_image),
                    dimensions=Image.open(tmp_image).size,
                )
                if tmp_image
                else None
            )

            image_2x_dto = (
                ComicImageDTO(
                    issue_number=issue_number,
                    path=tmp_image_2x,
                    format_=get_real_image_format(tmp_image_2x),
                    type_=ImageTypeEnum.ENLARGED,
                    dimensions=Image.open(tmp_image_2x).size,
                )
                if tmp_image_2x
                else None
            )

            if (image_dto and image_2x_dto) and (image_dto >= image_2x_dto):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Images conflict. Second image must be enlarged.",
                )

            for img_dto in (image_dto, image_2x_dto):
                if img_dto:
                    comic_create_dto.translation.images[img_dto.type_] = img_dto.db_path

            await self._uow.comic_repo.create(comic_create_dto)
            await self._uow.translation_repo.add(comic_create_dto.translation)
            for img_dto in (image_dto, image_2x_dto):
                if img_dto:
                    await ImageSaver(img_dto).save()
            await self._uow.commit()

            comic_model = await self._uow.comic_repo.get_by_issue_number(issue_number)

            return ComicGetDTO.from_model(comic_model)

    async def _generate_issue_number_if_not_exists(self, issue_number: int | None):
        if not issue_number:
            extra_num = await self._uow.comic_repo.get_extra_num()
            issue_number = 30_000 + extra_num
        return issue_number
