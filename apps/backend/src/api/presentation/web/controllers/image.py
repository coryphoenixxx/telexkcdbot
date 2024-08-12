from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, UploadFile
from starlette import status

from api.core.exceptions import (
    FileSizeLimitExceededError,
    UnsupportedImageFormatError,
    UploadImageIsNotExistsError,
)
from api.core.exceptions.image import UploadedImageReadError
from api.core.value_objects import TempImageUUID
from api.presentation.web.upload_image_manager import UploadImageManager

router = APIRouter(tags=["Images"], route_class=DishkaRoute)


@router.post(
    "/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": UploadImageIsNotExistsError | UploadedImageReadError
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
    *,
    upload_image_manager: Depends[UploadImageManager],
) -> TempImageUUID:
    return await upload_image_manager.read_to_temp(image_file)
