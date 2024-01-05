from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from starlette import status

from src.app.comics.images.utils import ImageFileSaver, UploadImageReader
from src.app.dependency_stubs import DatabaseHolderStub, ImageFileSaverStub, UploadImageReaderStub
from src.core.database import DatabaseHolder
from src.core.types import Language

from .dtos import TranslationImageDTO
from .exceptions import ImageBadMetadataError
from .services import TranslationImageService
from .types import TranslationImageId, TranslationImageVersion

router = APIRouter(
    tags=["Images"],
)


@router.post(
    "/comics/upload_image",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Either the issue number of the comic or its English title should be specified."
                           " Or file is empty",
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Unsupported image format.",
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "description": "The uploaded image exceeds the size limit.",
        },
    },
)
async def upload_images(
        image: Annotated[UploadFile, File()],
        issue_number: int | None = None,
        en_title: str | None = None,
        language: Language = Language.EN,
        version: TranslationImageVersion = TranslationImageVersion.DEFAULT,
        is_draft: bool = False,

        db_holder: DatabaseHolder = Depends(DatabaseHolderStub),
        upload_reader: UploadImageReader = Depends(UploadImageReaderStub),
        image_saver: ImageFileSaver = Depends(ImageFileSaverStub),
) -> TranslationImageId:
    if not issue_number and not en_title:
        raise ImageBadMetadataError

    tmp_image_obj = await upload_reader.read_one(image)

    image_dto = TranslationImageDTO(
        issue_number=issue_number,
        en_title=en_title,
        version=version,
        language=language,
        is_draft=is_draft,
        image_obj=tmp_image_obj,
    )

    image_id = await TranslationImageService(
        db_holder=db_holder,
        file_saver=image_saver,
    ).create(image_dto)

    return image_id
