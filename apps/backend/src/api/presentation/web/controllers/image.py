from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, UploadFile
from pydantic import HttpUrl
from starlette import status

from api.core.exceptions import (
    DownloadError,
    FileIsEmptyError,
    FileSizeLimitExceededError,
    UnsupportedImageFormatError,
    UploadedImageConflictError,
    UploadedImageIsNotExistsError,
)
from api.core.value_objects import TempImageID
from api.presentation.web.upload_image_manager import UploadImageManager

router = APIRouter(tags=["Images"], route_class=DishkaRoute)


@router.post(
    "/translations/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": FileIsEmptyError
            | UploadedImageIsNotExistsError
            | DownloadError
            | UploadedImageConflictError,
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "model": FileSizeLimitExceededError,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": UnsupportedImageFormatError,
        },
    },
)
async def upload_image(
    image_file: UploadFile | None = None,
    image_url: HttpUrl | None = None,
    *,
    upload_reader: Depends[UploadImageManager],
) -> TempImageID:
    return await upload_reader.read(image_file, image_url)
