from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, UploadFile
from starlette import status

from backend.application.image.exceptions import (
    ImageIsEmptyError,
    ImageSizeExceededLimitError,
)
from backend.application.image.services import UploadImageInteractor
from backend.domain.value_objects.image_file import ImageReadError, UnsupportedImageFormatError
from backend.presentation.api.controllers.schemas import TempImageSchema

router = APIRouter(tags=["Images"], route_class=DishkaRoute)


@router.post(
    "/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ImageIsEmptyError | ImageReadError,
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "model": ImageSizeExceededLimitError,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": UnsupportedImageFormatError,
        },
    },
)
async def upload_image(
    image_file: UploadFile | None = None,
    *,
    interactor: FromDishka[UploadImageInteractor],
) -> TempImageSchema:
    if image_file is None or image_file.filename is None:
        raise ImageIsEmptyError
    image_id = await interactor.execute(image_file)
    return TempImageSchema(image_id=image_id.value)
