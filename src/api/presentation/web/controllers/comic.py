import datetime

from fastapi import Depends, Response
from faststream.nats.fastapi import NatsRouter
from starlette import status

from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWithTranslationsDTO
from api.application.services.comic import ComicService
from api.application.types import ComicID, IssueNumber
from api.infrastructure.database.holder import DatabaseHolder
from api.infrastructure.database.types import DateRange, Limit, Offset, Order, QueryParams
from api.presentation.stub import Stub
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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_id(comic_id)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics/{number}", status_code=status.HTTP_200_OK)
async def get_comic_by_number(
    number: IssueNumber,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_number(number)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics/extras/{title}", status_code=status.HTTP_200_OK)
async def get_extra_comic_by_title(
    title: str,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicWithTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWithTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_extra_by_title(title)

    return ComicWithTranslationsResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    response: Response,
    page_size: int | None = None,
    page_num: int | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    order: Order = Order.ASC,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> list[ComicWithTranslationsResponseSchema]:
    comic_resp_dtos, total_count = await ComicService(
        db_holder=db_holder,
    ).get_list(
        QueryParams(
            limit=Limit(page_size) if page_num else None,
            offset=Offset(page_size * (page_num - 1)) if page_size and page_num else None,
            order=order,
            date_range=DateRange(start=date_from, end=date_to),
        ),
    )

    response.headers["X-Response-Count"] = str(len(comic_resp_dtos))
    response.headers["X-Total-Count"] = str(total_count)

    return [ComicWithTranslationsResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos]


@router.delete("/comics/{comic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comic(
    comic_id: ComicID,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
):
    await ComicService(db_holder=db_holder).delete(comic_id=comic_id)
