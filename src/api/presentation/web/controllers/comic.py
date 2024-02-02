from fastapi import Depends
from faststream.nats.fastapi import NatsRouter
from starlette import status

from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWithTranslationsDTO
from api.application.services.comic import ComicService
from api.application.types import ComicID, IssueNumber
from api.infrastructure.database import DatabaseHolder
from api.presentation.dependency_stubs import DatabaseHolderDepStub
from api.presentation.web.controllers.schemas.requests.comic import (
    ComicRequestSchema,
    ComicWithEnTranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses.comic import (
    ComicResponseSchema,
    ComicWithTranslationsResponseSchema,
)

router = NatsRouter(
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

    return ComicWithTranslationsResponseSchema.from_dto(comic_resp_dto)


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

    return ComicResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics/by_id/{comic_id}", status_code=status.HTTP_200_OK)
async def get_comic_by_id(
    comic_id: ComicID,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_id(comic_id)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics/{number}", status_code=status.HTTP_200_OK)
async def get_comic_by_number(
    number: IssueNumber,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_number(number)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics/extras/{title}", status_code=status.HTTP_200_OK)
async def get_extra_comic_by_title(
    title: str,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_extra_by_title(title)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> list[ComicWithTranslationsResponseSchema]:
    comic_resp_dtos: list[ComicResponseWithTranslationsDTO] = await ComicService(
        db_holder=db_holder,
    ).get_list()

    return [ComicWithTranslationsResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos]


@router.delete("/comics/{comic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comic(
    comic_id: ComicID,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
):
    await ComicService(db_holder=db_holder).delete(comic_id=comic_id)
