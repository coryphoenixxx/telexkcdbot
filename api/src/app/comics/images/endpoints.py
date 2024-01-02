from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette import status

from src.core.database import db
from src.core.types import Language

from .dtos import TranslationImageDTO
from .repo import TranslationImageRepo
from .services import TranslationImageService
from .types import ImageVersion
from .utils import ImageFileSaveHelper, UploadImageReader

router = APIRouter(
    tags=["Images"],
)


@router.post("/comics/upload_image")
async def upload_images(
        image: Annotated[UploadFile, File()],
        issue_number: int | None = None,
        en_title: str | None = None,
        language: Language = Language.EN,
        version: ImageVersion = ImageVersion.DEFAULT,
        is_draft: bool = False,
        session_factory: sessionmaker[AsyncSession] = Depends(db.get_session_factory),
) -> int:
    if not issue_number and not en_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either the issue number of the comic or its English title should be specified.",
        )

    temp_image_obj = await UploadImageReader().read_one(image)

    image_dto = TranslationImageDTO(
        issue_number=issue_number,
        en_title=en_title,
        version=version,
        language=language,
        is_draft=is_draft,
        image_obj=temp_image_obj,
    )

    image_id = await TranslationImageService(
        repo=TranslationImageRepo(
            session=session_factory(),
        ),
        file_saver=ImageFileSaveHelper(),
    ).create(image_dto)

    return image_id
