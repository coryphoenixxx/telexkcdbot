from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.database import db
from src.core.utils.uow import UOW

from .dtos import ComicGetDTO
from .image_utils.reader import ImageReader
from .schemas import ComicCreateSchema
from .services import ComicsService

router = APIRouter(
    prefix="/comics",
    tags=["Comics"],
)

COMIC_EXAMPLE_JSON = """
{
    "issue_number": 1,
    "publication_date": "2010-10-10",
    "xkcd_url": "https://xkcd.com/1",
    "reddit_url": "https://www.reddit.com/r/xkcd/comments/abc/xkcd_1",
    "explain_url": "https://www.explainxkcd.com/wiki/index.php/1",
    "link_on_click": "https://www.example.com/",
    "is_interactive": false,
    "is_extra": false,
    "tags": ["Tag1", "Tag2"],
    "title": "Some Title",
    "tooltip": "Some tooltip",
    "transcript": "Some transcript",
    "news_block": "Some news"
}
"""


@router.post("")
async def create_comic(
    comic_json_data: Annotated[
        Json[ComicCreateSchema],
        Form(
            description=f"<textarea>Example: {COMIC_EXAMPLE_JSON}</textarea>",
        ),
    ],
    image: Annotated[UploadFile, File()] = None,
    image_2x: Annotated[UploadFile, File()] = None,
    session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
    image_reader: ImageReader = Depends(),
):
    comic_get_dto: ComicGetDTO = await ComicsService(uow=UOW(session_factory)).create_comic(
        comic_create_schema=comic_json_data,
        tmp_image=await image_reader.read(image),
        tmp_image_2x=await image_reader.read(image_2x),
    )

    return comic_get_dto
