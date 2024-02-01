from typing import Annotated

from fastapi import Depends, File, Query, UploadFile
from faststream.nats import JStream, NatsBroker
from faststream.nats.fastapi import NatsRouter
from pydantic import HttpUrl
from shared.types import ImageProcessOutMessage
from starlette import status
from yarl import URL

from api.application.dependency_stubs import (
    BrokerDepStub,
    DatabaseHolderDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from api.application.images.utils import ImageSaveHelper, UploadImageHandler
from api.core.database import DatabaseHolder
from api.core.types import Language

from .dtos import TranslationImageMeta
from .exceptions import (
    NoImageError,
    OneTypeImageError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadExceedLimitError,
)
from .service import TranslationImageService
from .types import TranslationImageID

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
    title: Annotated[str, Query(max_length=50)],
    number: Annotated[int | None, Query(gt=0)] = None,
    language: Language = Language.EN,
    is_draft: bool = False,
    image_file: Annotated[UploadFile, File(...)] = None,
    image_url: HttpUrl | None = None,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
    upload_reader: UploadImageHandler = Depends(UploadImageReaderDepStub),
    image_saver: ImageSaveHelper = Depends(ImageFileSaverDepStub),
    broker: NatsBroker = Depends(BrokerDepStub),
) -> TranslationImageID:
    match (image_url, image_file):
        case (None, None):
            raise NoImageError
        case (None, file):
            image_obj = await upload_reader.read(file)
        case (url, None):
            image_obj = await upload_reader.download(URL(str(url)))
        case _:
            raise OneTypeImageError

    image_id = await TranslationImageService(
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

    return image_id


stream = JStream(name="stream", declare=False)


@router.subscriber("processed_images", queue="processed_images_queue", stream=stream)
async def base_handler(
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
