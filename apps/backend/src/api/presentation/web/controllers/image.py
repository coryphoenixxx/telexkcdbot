from typing import Annotated

from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, File, Query, UploadFile
from pydantic import HttpUrl, constr
from starlette import status

from api.application.exceptions.image import (
    DownloadingImageError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadedImageError,
    UploadedImageTypeConflictError,
    UploadExceedSizeLimitError,
)
from api.application.services import TranslationImageService
from api.my_types import Language
from api.presentation.my_types import TranslationImageMeta
from api.presentation.upload_reader import UploadImageHandler
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageOrphanResponseSchema,
)

router = APIRouter(tags=["Images"], route_class=DishkaRoute)


@router.post(
    "/translations/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": RequestFileIsEmptyError
            | UploadedImageError
            | DownloadingImageError
            | UploadedImageTypeConflictError,
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "model": UploadExceedSizeLimitError,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": UnsupportedImageFormatError,
        },
    },
)
async def upload_image(
    title: constr(min_length=1, strip_whitespace=True),
    number: Annotated[int | None, Query(ge=1)] = None,
    language: Language = Language.EN,
    is_draft: bool = False,
    image_file: Annotated[UploadFile, File(...)] = None,
    image_url: HttpUrl | None = None,
    *,
    upload_reader: Depends[UploadImageHandler],
    service: Depends[TranslationImageService],
) -> TranslationImageOrphanResponseSchema:
    if image_file and image_url:
        raise UploadedImageTypeConflictError
    elif image_file is None and image_url is None:
        raise UploadedImageError
    else:
        image_obj = (
            await upload_reader.read(image_file)
            if image_file
            else await upload_reader.download(str(image_url))
        )

    image_resp_dto = await service.create(
        metadata=TranslationImageMeta(
            number=number,
            title=title,
            language=language,
            is_draft=is_draft,
        ),
        image=image_obj,
    )

    return TranslationImageOrphanResponseSchema(
        id=image_resp_dto.id,
        original=image_resp_dto.original_rel_path,
    )


# from faststream.nats import JStream, PullSub
# from shared.messages import ImageProcessOutMessage
#
# @router.subscriber(
#     "internal.api.images.process.out",
#     queue="process_images_out_queue",
#     stream=JStream(
#         name="process_images_out_stream",
#         max_age=600,
#     ),
#     pull_sub=PullSub(),
#     durable="api",
# )
# @inject
# async def processed_images_handler(
#     msg: ImageProcessOutMessage,
#     *,
#     service: FromDishka[TranslationImageService],
# ):
#     await service.update(
#         image_id=msg.image_id,
#         converted_abs_path=msg.converted_abs_path,
#         thumbnail_abs_path=msg.thumbnail_abs_path,
#     )
