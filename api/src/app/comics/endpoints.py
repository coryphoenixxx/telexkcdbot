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

COMIC_EXAMPLE_JSON = (
    "{"
    '"issue_number": 1, '
    '"publication_date": "2010-10-10", '
    '"xkcd_url": "https://xkcd.com/1", '
    '"explain_url": "https://www.explainxkcd.com/wiki/index.php/1", '
    '"reddit_url": "https://www.reddit.com/r/xkcd/comments/abc/xkcd_1", '
    '"link_on_click": "https://www.example.com/", '
    '"is_interactive": false, '
    '"is_extra": false, '
    '"tags": ["Tag1", "Tag2"], '
    '"title": "Some Title", '
    '"tooltip": "Some tooltip", '
    '"transcript": "Some transcript", '
    '"news_block": "Some news"'
    "}"
)


@router.post("")
async def create_comic(
    data: Annotated[
        Json[ComicCreateSchema],
        Form(
            description=f"Example: {COMIC_EXAMPLE_JSON}",
        ),
    ],
    image: Annotated[UploadFile | None, File()] = None,
    image_2x: Annotated[UploadFile | None, File()] = None,
    session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
    image_reader: ImageReader = Depends(),
):
    comic_dto = data.to_dto()

    temp_image, temp_image_2x = (
        await image_reader.read(
            image,
            comic_dto.issue_number,
        ),
        await image_reader.read(
            image_2x,
            comic_dto.issue_number,
            img_type=ComicImageType.ENLARGED,
        ),
    )

    if (temp_image and temp_image_2x) and (temp_image >= temp_image_2x):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Images conflict. Second image must be enlarged.",
        )

    await ComicsService(uow=UOW(session_factory)).create_comic(
        comic_dto=comic_dto,
        images=[img for img in (temp_image, temp_image_2x) if img],
    )
