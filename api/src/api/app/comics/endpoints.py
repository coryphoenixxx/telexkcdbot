from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette import status

from api.app.comics.image_utils.reader import ImageReader
from api.app.comics.image_utils.types import ComicImageType
from api.core.database import db
from api.core.utils.uow import UOW

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
        Form(description='Example: {"comic_id": 1, "title": "Some title", "publication_date": "2010-10-10"}'),
    ],
    image: Annotated[UploadFile | None, File()] = None,
    image_2x: Annotated[UploadFile | None, File()] = None,
    session_factory: async_sessionmaker[AsyncSession] = Depends(db.session_factory),
    image_reader: ImageReader = Depends(),
):
    comic_dto = data.to_dto()
    temp_image, temp_image_2x = (
        await image_reader.read(image, comic_dto.comic_id),
        await image_reader.read(image_2x, comic_dto.comic_id, img_type=ComicImageType.ENLARGED),
    )

    if temp_image and temp_image_2x and temp_image >= temp_image_2x:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Images conflict. Second image must be enlarged.",
        )

    await ComicsService(uow=UOW(session_factory)).create_comic(
        comic_dto=comic_dto,
        temp_images=[temp_image, temp_image_2x],
    )
