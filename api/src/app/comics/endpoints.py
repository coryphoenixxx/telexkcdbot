from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette import status

from src.core.database import db
from src.core.utils.uow import UOW

from .dtos import ComicGetDTO, ComicTotalDTO
from .image_utils.upload_reader import UploadImageReader
from .schemas import ComicCreateSchema
from .services import ComicsService

router = APIRouter(
    tags=["Comics"],
)

COMIC_EXAMPLE_JSON_DESC = """
<textarea>Example
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
</textarea>
"""


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
        comic_json_data: Annotated[
            Json[ComicCreateSchema],
            Form(
                description=COMIC_EXAMPLE_JSON_DESC,
            ),
        ],
        image: Annotated[UploadFile, File()] = None,
        image_2x: Annotated[UploadFile, File()] = None,
        session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
):
    image_obj, image_2x_obj = await UploadImageReader().read(image, image_2x)

    comic_dto = ComicTotalDTO.from_request_data(comic_json_data, image_obj, image_2x_obj)

    comic_get_dto: ComicGetDTO = await ComicsService(
        uow=UOW(session_factory),
    ).create_comic(
        comic_dto=comic_dto,
    )

    return comic_get_dto


@router.get("/comics/{issue_number}")
async def get_comic_by_issue_number(
        issue_number: int,
        session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
):
    comic_get_dto = await ComicsService(
        uow=(UOW(session_factory)),
    ).get_comic_by_issue_number(issue_number)

    if not comic_get_dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comic with issue_number {issue_number} doesn't exists.",
        )
    return comic_get_dto
