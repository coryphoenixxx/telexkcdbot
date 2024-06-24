from typing import Annotated

from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, File, Query, UploadFile
from faststream.nats import NatsBroker
from pydantic import HttpUrl, constr
from shared.messages import ImageProcessInMessage
from starlette import status

from api.application.dtos.common import Language, TranslationImageMeta
from api.application.services import TranslationImageService
from api.core.exceptions import (
    DownloadingImageError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadedImageError,
    UploadedImageTypeConflictError,
    UploadExceedSizeLimitError,
)
from api.presentation.web.controllers.schemas.responses import (
    TranslationImageOrphanResponseSchema,
)
from api.presentation.web.upload_reader import UploadImageHandler

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
    is_draft: bool = False,  # noqa: FBT001, FBT002
    image_file: Annotated[UploadFile, File(...)] = None,
    image_url: HttpUrl | None = None,
    *,
    upload_reader: Depends[UploadImageHandler],
    service: Depends[TranslationImageService],
    broker: Depends[NatsBroker],
) -> TranslationImageOrphanResponseSchema:
    if image_file and image_url:
        raise UploadedImageTypeConflictError

    if image_file is None and image_url is None:
        raise UploadedImageError

    image_obj = (
        await upload_reader.read(image_file)
        if image_file
        else await upload_reader.download(str(image_url))
    )

    original_abs_path, image_resp_dto = await service.create(
        metadata=TranslationImageMeta(
            number=number,
            title=title,
            language=language,
            is_draft=is_draft,
        ),
        image=image_obj,
    )

    await broker.publish(
        message=ImageProcessInMessage(
            image_id=image_resp_dto.id,
            original_abs_path=original_abs_path,
        ),
        subject="internal.api.images.process.in",
        stream="process_images_in_stream",
    )

    return TranslationImageOrphanResponseSchema(
        id=image_resp_dto.id,
        original=str(image_resp_dto.original_rel_path),
    )
