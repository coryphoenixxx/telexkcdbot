from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette import status

from src.core.database import db
from src.core.database.uow import UOW

from .dtos import ComicCreateTotalDTO, ComicGetDTO
from .schemas import ComicCreateSchema
from .services import ComicsService

router = APIRouter(
    tags=["Comics"],
)


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
        comic_json_data: ComicCreateSchema,
        session_factory: async_sessionmaker[AsyncSession] = Depends(db.get_session_factory),
):
    comic_dto = ComicCreateTotalDTO.from_request_data(comic_json_data)

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
