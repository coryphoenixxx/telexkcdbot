from fastapi import APIRouter, Depends
from starlette import status

from src.app.dependency_stubs import DatabaseHolderDepStub
from src.core.database import DatabaseHolder

from .dtos.response import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .schemas.request import ComicRequestSchema, ComicWithEnTranslationRequestSchema
from .schemas.response import ComicResponseSchema, ComicWithTranslationsResponseSchema
from .service import ComicService
from .types import ComicID

router = APIRouter(
    tags=["Comics"],
)


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
    schema: ComicWithEnTranslationRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_req_dto, en_translation_req_dto = schema.to_dtos()

    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).create(comic_req_dto, en_translation_req_dto)

    return comic_resp_dto.to_schema()


@router.put("/comics/{comic_id}", status_code=status.HTTP_200_OK)
async def update_comic(
    comic_id: ComicID,
    schema: ComicRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await ComicService(
        db_holder=db_holder,
    ).update(
        comic_id=comic_id,
        comic_req_dto=schema.to_dto(),
    )

    return comic_resp_dto.to_schema()


@router.get("/comics/by_id/{comic_id}", status_code=status.HTTP_200_OK)
async def get_comic_by_id(
    comic_id: ComicID,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_id(comic_id)

    return comic_resp_dto.to_schema()


@router.get("/comics/{issue_number}", status_code=status.HTTP_200_OK)
async def get_comic_by_issue_number(
    issue_number: int,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_issue_number(issue_number)

    return comic_resp_dto.to_schema()


@router.get("/comics/extras/{title}", status_code=status.HTTP_200_OK)
async def get_extra_comic_by_title(
    title: str,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_extra_by_title(title)

    return comic_resp_dto.to_schema()


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> list[ComicWithTranslationsResponseSchema]:
    comic_resp_dtos: list[ComicResponseWithTranslationsDTO] = await ComicService(
        db_holder=db_holder,
    ).get_list()

    return [dto.to_schema() for dto in comic_resp_dtos]


@router.delete("/comics/{comic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comic(
    comic_id: ComicID,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
):
    await ComicService(db_holder=db_holder).delete(comic_id=comic_id)
