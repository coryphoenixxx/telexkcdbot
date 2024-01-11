from fastapi import APIRouter, Depends
from starlette import status

from src.app.dependency_stubs import DatabaseHolderDep
from src.core.database import DatabaseHolder

from .dtos.responses import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .schemas.requests import ComicRequestSchema, ComicWithEnTranslationRequestSchema
from .schemas.responses import ComicResponseSchema, ComicWithTranslationsResponseSchema
from .services import ComicService
from .types import ComicID

router = APIRouter(
    tags=["Comics"],
)


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
    schema: ComicWithEnTranslationRequestSchema,
    holder: DatabaseHolder = Depends(DatabaseHolderDep),
) -> ComicWithTranslationsResponseSchema:
    comic_req_dto, en_translation_req_dto = schema.to_dtos()

    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        holder=holder,
    ).create(comic_req_dto, en_translation_req_dto)

    return comic_resp_dto.to_schema()


@router.put("/comics/{comic_id}", status_code=status.HTTP_200_OK)
async def update_comic(
    comic_id: ComicID,
    schema: ComicRequestSchema,
    holder: DatabaseHolder = Depends(DatabaseHolderDep),
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await ComicService(
        holder=holder,
    ).update(
        comic_id=comic_id,
        comic_req_dto=schema.to_dto(),
    )

    return comic_resp_dto.to_schema()


@router.get("/comics/get_by_id/{comic_id}", status_code=status.HTTP_200_OK)
async def get_comic_by_id(
    comic_id: ComicID,
    holder: DatabaseHolder = Depends(DatabaseHolderDep),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        holder=holder,
    ).get_by_id(comic_id)

    return comic_resp_dto.to_schema()
