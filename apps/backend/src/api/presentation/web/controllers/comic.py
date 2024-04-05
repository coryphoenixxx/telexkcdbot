import datetime

from fastapi import Depends
from fastapi.params import Query
from faststream.nats.fastapi import NatsRouter
from shared.types import Order
from starlette import status

from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.exceptions.comic import (
    ComicByIDNotFoundError,
    ComicByIssueNumberNotFoundError,
    ComicBySlugNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from api.application.exceptions.translation import (
    TranslationImagesAlreadyAttachedError,
    TranslationImagesNotCreatedError,
)
from api.application.services.comic import ComicService
from api.application.types import ComicID, IssueNumber, LanguageCode, TotalCount
from api.infrastructure.database.holder import DatabaseHolder
from api.infrastructure.database.types import ComicFilterParams, DateRange, Limit, Offset
from api.presentation.stub import Stub
from api.presentation.web.controllers.schemas.requests.comic import ComicRequestSchema
from api.presentation.web.controllers.schemas.responses.comic import (
    ComicResponseSchema,
    ComicsWithMetadata,
    ComicWTranslationsResponseSchema,
    Pagination,
)

router = NatsRouter(
    tags=["Comics"],
)


@router.post(
    "/comics",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ComicNumberAlreadyExistsError | ExtraComicTitleAlreadyExistsError,
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": TranslationImagesNotCreatedError | TranslationImagesAlreadyAttachedError,
        },
    },
)
async def create_comic(
    schema: ComicRequestSchema,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await ComicService(
        db_holder=db_holder,
    ).create(schema.to_dto())

    return ComicResponseSchema.from_dto(comic_resp_dto)


@router.put(
    "/comics/{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIDNotFoundError,
        },
        status.HTTP_409_CONFLICT: {
            "model": ComicNumberAlreadyExistsError,
        },
    },
)
async def update_comic(
    comic_id: ComicID,
    schema: ComicRequestSchema,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await ComicService(
        db_holder=db_holder,
    ).update(comic_id, schema.to_dto())

    return ComicResponseSchema.from_dto(comic_resp_dto)


@router.delete(
    "/comics/{comic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIDNotFoundError,
        },
    },
)
async def delete_comic(
    comic_id: ComicID,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
):
    await ComicService(db_holder=db_holder).delete(comic_id=comic_id)


@router.get(
    "/comics/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIDNotFoundError,
        },
    },
)
async def get_comic_by_id(
    comic_id: ComicID,
    langs: list[LanguageCode.NON_ENGLISH] = Query(default=None),
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_id(comic_id)

    if langs:
        return ComicWTranslationsResponseSchema.from_dto(
            dto=comic_resp_dto,
            filter_languages=langs,
        )
    return ComicResponseSchema.from_dto(dto=comic_resp_dto)


@router.get(
    "/comics/{number:int}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIssueNumberNotFoundError,
        },
    },
)
async def get_comic_by_issue_number(
    number: IssueNumber,
    langs: list[LanguageCode.NON_ENGLISH] = Query(default=None),
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_issue_number(number)

    if langs:
        return ComicWTranslationsResponseSchema.from_dto(
            dto=comic_resp_dto,
            filter_languages=langs,
        )
    return ComicResponseSchema.from_dto(dto=comic_resp_dto)


@router.get(
    "/comics/{slug:str}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicBySlugNotFoundError,
        },
    },
)
async def get_by_slug(
    slug: str,
    langs: list[LanguageCode.NON_ENGLISH] = Query(default=None),
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_slug(slug)

    if langs:
        return ComicWTranslationsResponseSchema.from_dto(
            dto=comic_resp_dto,
            filter_languages=langs,
        )
    return ComicResponseSchema.from_dto(dto=comic_resp_dto)


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    limit: int | None = None,
    page: int | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    order: Order = Order.ASC,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicsWithMetadata:
    limit = Limit(limit) if page else None
    offset = Offset(limit * (page - 1)) if limit and page else None

    comic_resp_dtos = await ComicService(
        db_holder=db_holder,
    ).get_list(
        ComicFilterParams(
            limit=limit,
            offset=offset,
            order=order,
            date_range=DateRange(start=date_from, end=date_to),
        ),
    )

    return ComicsWithMetadata(
        meta=Pagination(
            total=TotalCount(len(comic_resp_dtos)),
            limit=limit,
            offset=offset,
        ),
        data=[ComicWTranslationsResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos],
    )
