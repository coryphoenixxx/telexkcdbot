import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import HttpUrl
from shared.http_client import HttpClient
from starlette import status

from api.application.dependency_stubs import (
    DatabaseHolderDepStub,
    HttpClientDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from api.application.images.utils import ImageFileSaver, UploadImageReader
from api.core.database import DatabaseHolder
from api.core.types import Language

from .dtos import TranslationImageRequestDTO
from .exceptions import (
    NoImageError,
    OneTypeImageError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadExceedLimitError,
)
from .service import TranslationImageService
from .types import TranslationImageID, TranslationImageVersion

router = APIRouter(
    tags=["Images"],
)


@router.post(
    "/comics/upload_image",
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
async def upload_images(
    title: Annotated[str, Query(max_length=50)],
    image_file: Annotated[UploadFile, File(...)] = None,
    image_url: HttpUrl | None = None,
    number: Annotated[int | None, Query(gt=0)] = None,
    language: Language = Language.EN,
    version: TranslationImageVersion = TranslationImageVersion.DEFAULT,
    is_draft: bool = False,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
    upload_reader: UploadImageReader = Depends(UploadImageReaderDepStub),
    image_saver: ImageFileSaver = Depends(ImageFileSaverDepStub),
    client: HttpClient = Depends(HttpClientDepStub),
) -> TranslationImageID:
    match (image_url, image_file):
        case (None, None):
            raise NoImageError
        case (None, file):
            tmp_image_obj = await upload_reader.read(file)
        case (url, None):
            await asyncio.sleep(1)
            tmp_image_obj = await upload_reader.download(client, str(url))
        case (url, file):
            raise OneTypeImageError
        case _:
            tmp_image_obj = None

    image_id = await TranslationImageService(
        db_holder=db_holder,
        image_saver=image_saver,
    ).create(
        image_dto=TranslationImageRequestDTO(
            number=number,
            title=title,
            version=version,
            language=language,
            is_draft=is_draft,
            image=tmp_image_obj,
        ),
    )

    return image_id