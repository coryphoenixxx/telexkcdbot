from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, UploadFile
from starlette import status

from backend.infrastructure.upload_image_manager import (
    UnsupportedImageFormatError,
    UploadedImageReadError,
    UploadImageIsEmptyError,
    UploadImageManager,
    UploadImageSizeExceededLimitError,
)
from backend.presentation.api.controllers.schemas import TempImageSchema

router = APIRouter(tags=["Images"], route_class=DishkaRoute)


@router.post(
    "/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": UploadImageIsEmptyError | UploadedImageReadError
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "model": UploadImageSizeExceededLimitError,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": UnsupportedImageFormatError,
        },
    },
)
async def upload_image(
    image_file: UploadFile | None = None,
    *,
    upload_image_manager: FromDishka[UploadImageManager],
) -> TempImageSchema:
    if image_file is None or image_file.filename is None:
        raise UploadImageIsEmptyError

    return TempImageSchema(temp_image_id=await upload_image_manager.read_from_stream(image_file))
