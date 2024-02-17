from typing import Annotated

from fastapi import Depends, File, Query, UploadFile
from faststream.nats import NatsBroker
from faststream.nats.fastapi import NatsRouter
from pydantic import HttpUrl
from shared.messages import ImageProcessOutMessage
from shared.types import LanguageCode
from starlette import status

from api.application.exceptions.image import (
    ImageOneTypeError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadedImageError,
    UploadExceedLimitError,
)
from api.application.image_saver import ImageSaveHelper
from api.application.services import TranslationImageService
from api.application.types import TranslationImageID
from api.infrastructure.database.holder import DatabaseHolder
from api.presentation.dependency_stubs import (
    BrokerDepStub,
    DatabaseHolderDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from api.presentation.types import TranslationImageMeta
from api.presentation.upload_reader import UploadImageHandler
from api.presentation.web.controllers.schemas.responses.image import TranslationImageResponseSchema

router = NatsRouter(
    tags=["Images"],
)


@router.post(
    "/translations/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": RequestFileIsEmptyError.message,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": UnsupportedImageFormatError.message,
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "description": UploadExceedLimitError.message,
        },
    },
)
async def upload_image(
    title: str,
    number: Annotated[int | None, Query(gt=0)] = None,
    language: LanguageCode = LanguageCode.EN,
    is_draft: bool = False,
    image_file: Annotated[UploadFile, File(...)] = None,
    image_url: HttpUrl | None = None,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
    upload_reader: UploadImageHandler = Depends(UploadImageReaderDepStub),
    image_saver: ImageSaveHelper = Depends(ImageFileSaverDepStub),
    broker: NatsBroker = Depends(BrokerDepStub),
) -> TranslationImageResponseSchema:
    match (image_url, image_file):
        case (None, None):
            raise UploadedImageError
        case (None, file):
            image_obj = await upload_reader.read(file)
        case (url, None):
            image_obj = await upload_reader.download(str(url))
        case _:
            raise ImageOneTypeError

    image_resp_dto = await TranslationImageService(
        db_holder=db_holder,
        image_saver=image_saver,
        broker=broker,
    ).create(
        meta=TranslationImageMeta(
            number=number,
            title=title,
            language=language,
            is_draft=is_draft,
        ),
        image=image_obj,
    )

    return TranslationImageResponseSchema(
        id=image_resp_dto.id,
        original=image_resp_dto.original_rel_path,
    )


@router.subscriber(
    "internal.api.images.process.out",
    queue="process_images_out_queue",
    stream="process_images_out_stream",
)
async def processed_images_handler(
    msg: ImageProcessOutMessage,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
    image_saver: ImageSaveHelper = Depends(ImageFileSaverDepStub),
):
    await TranslationImageService(
        db_holder=db_holder,
        image_saver=image_saver,
    ).update(
        image_id=TranslationImageID(msg.image_id),
        converted_abs_path=msg.converted_abs_path,
        thumbnail_abs_path=msg.thumbnail_abs_path,
    )
