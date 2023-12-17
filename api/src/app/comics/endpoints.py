from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette import status

from src.core.database import db
from src.core.utils.uow import UOW

from .image_utils.reader import ImageReader
from .image_utils.types import ComicImageType
from .schemas import ComicCreateSchema
from .services import ComicsService

router = APIRouter(
    prefix="/comics",
    tags=["Comics"],
)


@router.post("")
async def create_comic(
        data: Annotated[
            Json[ComicCreateSchema],
            Form(
                description='Example: {"issue_number": 1, "title": "Some title", "publication_date": "2010-10-10"}',
            ),
        ],
        image: Annotated[UploadFile | None, File()] = None,
        image_2x: Annotated[UploadFile | None, File()] = None,
        session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
        image_reader: ImageReader = Depends(),
):
    comic_base_dto, comic_eng_translation_dto = data.to_dtos()
    temp_image, temp_image_2x = (
        await image_reader.read(image, comic_base_dto.issue_number),
        await image_reader.read(image_2x, comic_base_dto.issue_number, img_type=ComicImageType.ENLARGED),
    )

    if (temp_image and temp_image_2x) and (temp_image >= temp_image_2x):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Images conflict. Second image must be enlarged.",
        )

    await ComicsService(uow=UOW(session_factory)).create_comic(
        comic_base_dto=comic_base_dto,
        comic_eng_translation_dto=comic_eng_translation_dto,
        temp_images=[temp_image, temp_image_2x],
    )
