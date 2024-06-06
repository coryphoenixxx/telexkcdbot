import datetime

from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from fastapi.params import Query
from shared.my_types import Order
from starlette import status

from api.application.dtos.common import (
    ComicFilterParams,
    DateRange,
    Language,
    Limit,
    Offset,
    Tag,
    TagParam,
)
from api.application.dtos.responses import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.exceptions.comic import (
    ComicByIDNotFoundError,
    ComicByIssueNumberNotFoundError,
    ComicBySlugNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from api.application.exceptions.translation import (
    ImagesAlreadyAttachedError,
    ImagesNotCreatedError,
)
from api.application.services.comic import ComicService
from api.core.entities import ComicID, IssueNumber
from api.presentation.web.controllers.schemas.requests import ComicRequestSchema
from api.presentation.web.controllers.schemas.responses import (
    ComicResponseSchema,
    ComicsWMetadata,
    ComicWTranslationsResponseSchema,
    PaginationSchema,
)

router = APIRouter(tags=["Comics"], route_class=DishkaRoute)


@router.post(
    "/comics",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ImagesNotCreatedError | ImagesAlreadyAttachedError,
        },
        status.HTTP_409_CONFLICT: {
            "model": ComicNumberAlreadyExistsError | ExtraComicTitleAlreadyExistsError,
        },
    },
)
async def create_comic(
    schema: ComicRequestSchema,
    *,
    service: Depends[ComicService],
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await service.create(schema.to_dto())

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
    service: Depends[ComicService],
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseDTO = await service.update(comic_id, schema.to_dto())

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
    service: Depends[ComicService],
):
    await service.delete(comic_id=comic_id)


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
    *,
    service: Depends[ComicService],
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_id(comic_id)

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
    *,
    service: Depends[ComicService],
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_issue_number(number)

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
async def get_comic_by_slug(
    slug: str,
    *,
    service: Depends[ComicService],
) -> ComicResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_slug(slug)

    return ComicResponseSchema.from_dto(dto=comic_resp_dto)


@router.get(
    "/comics-with-translations/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIDNotFoundError,
        },
    },
)
async def get_comic_with_translations_by_id(
    comic_id: ComicID,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: Depends[ComicService],
) -> ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_id(comic_id)

    return ComicWTranslationsResponseSchema.from_dto(
        dto=comic_resp_dto,
        filter_languages=languages,
    )


@router.get(
    "/comics-with-translations/{number:int}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicByIssueNumberNotFoundError,
        },
    },
)
async def get_comic_with_translations_by_issue_number(
    number: IssueNumber,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: Depends[ComicService],
) -> ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_issue_number(number)

    return ComicWTranslationsResponseSchema.from_dto(
        dto=comic_resp_dto,
        filter_languages=languages,
    )


@router.get(
    "/comics-with-translations/{slug:str}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicBySlugNotFoundError,
        },
    },
)
async def get_comic_with_translations_by_slug(
    slug: str,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: Depends[ComicService],
) -> ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await service.get_by_slug(slug)

    return ComicWTranslationsResponseSchema.from_dto(
        dto=comic_resp_dto,
        filter_languages=languages,
    )


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    q: str = Query(min_length=1, max_length=50, default=None),
    page_size: int | None = Query(None, alias="psize"),
    page_num: int | None = Query(None, alias="pnum"),
    date_from: datetime.date | None = Query(None),
    date_to: datetime.date | None = Query(None),
    order: Order = Order.ASC,
    tags: list[Tag] = Query(None, alias="tag"),
    tag_param: TagParam | None = None,
    *,
    service: Depends[ComicService],
) -> ComicsWMetadata:
    limit = Limit(page_size) if page_num else None
    offset = Offset(limit * (page_num - 1)) if limit and page_num else None

    total, comic_resp_dtos = await service.get_list(
        ComicFilterParams(
            q=q,
            limit=limit,
            offset=offset,
            order=order,
            date_range=DateRange(start=date_from, end=date_to),
            tags=tags,
            tag_param=tag_param,
        ),
    )

    return ComicsWMetadata(
        meta=PaginationSchema(
            total=total,
            limit=limit,
            offset=offset,
        ),
        data=[ComicResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos],
    )
