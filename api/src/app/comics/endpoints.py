from fastapi import APIRouter, Depends
from starlette import status

from src.app.dependency_stubs import DatabaseHolderStub
from src.core.database import DatabaseHolder

from .dtos import ComicCreateTotalDTO, ComicGetDTO
from .schemas import ComicCreateSchema
from .services import ComicService

router = APIRouter(
    tags=["Comics"],
)


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
        comic_json_data: ComicCreateSchema,
        holder: DatabaseHolder = Depends(DatabaseHolderStub),
):
    comic_dto = ComicCreateTotalDTO.from_request(comic_json_data)

    comic_get_dto: ComicGetDTO = await ComicService(
        holder=holder,
    ).create_comic(comic_dto=comic_dto)

    return comic_get_dto


@router.get("/comics/get_by_id/{comic_id}")
async def get_comic_by_id(
        comic_id: int,
        holder: DatabaseHolder = Depends(DatabaseHolderStub),
):
    comic_get_dto = await ComicService(
        holder=holder,
    ).get_comic_by_id(comic_id)

    return comic_get_dto
