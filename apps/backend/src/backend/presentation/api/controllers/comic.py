import datetime
from typing import Annotated

from annotated_types import MaxLen, MinLen
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query
from pydantic import PositiveInt
from starlette import status

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
    TempImageNotFoundError,
)
from backend.application.comic.services import (
    ComicReader,
    CreateComicInteractor,
    DeleteComicInteractor,
    FullUpdateComicInteractor,
)
from backend.application.common.pagination import (
    ComicFilterParams,
    DateRange,
    Limit,
    Offset,
    Order,
    TagParam,
)
from backend.core.value_objects import ComicID, IssueNumber, Language, TagName
from backend.presentation.api.controllers.schemas import (
    ComicRequestSchema,
    ComicResponseSchema,
    ComicsWMetadata,
    ComicWTranslationsResponseSchema,
    PaginationSchema,
    TranslationWLanguageResponseSchema,
)

router = APIRouter(tags=["Comics"], route_class=DishkaRoute)


@router.post(
    "/comics",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": TempImageNotFoundError},
        status.HTTP_409_CONFLICT: {
            "model": ComicNumberAlreadyExistsError | ExtraComicTitleAlreadyExistsError
        },
    },
)
async def create_comic(
    schema: ComicRequestSchema,
    *,
    service: FromDishka[CreateComicInteractor],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_dto(await service.execute(schema.to_dto()))


@router.put(
    "/comics/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
        status.HTTP_409_CONFLICT: {"model": ComicNumberAlreadyExistsError},
    },
)
async def update_comic(
    comic_id: int,
    schema: ComicRequestSchema,
    *,
    service: FromDishka[FullUpdateComicInteractor],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_dto(await service.execute(ComicID(comic_id), schema.to_dto()))


@router.delete(
    "/comics/{comic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def delete_comic(
    comic_id: int,
    *,
    service: FromDishka[DeleteComicInteractor],
) -> None:
    await service.execute(comic_id=ComicID(comic_id))


@router.get(
    "/comics/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_by_id(
    comic_id: int,
    *,
    service: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_dto(dto=await service.get_by_id(ComicID(comic_id)))


@router.get(
    "/comics/{number:int}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_by_issue_number(
    number: int,
    *,
    service: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_dto(dto=await service.get_by_issue_number(IssueNumber(number)))


@router.get(
    "/comics/{slug:str}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_by_slug(
    slug: str,
    *,
    service: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_dto(dto=await service.get_by_slug(slug))


@router.get(
    "/comics-with-translations/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_with_translations_by_id(
    comic_id: int,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_dto(
        dto=await service.get_by_id(ComicID(comic_id)),
        filter_languages=languages,
    )


@router.get(
    "/comics-with-translations/{number:int}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_with_translations_by_issue_number(
    number: int,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_dto(
        dto=await service.get_by_issue_number(IssueNumber(number)),
        filter_languages=languages,
    )


@router.get(
    "/comics-with-translations/{slug:str}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_with_translations_by_slug(
    slug: str,
    languages: list[Language] = Query(default=None, alias="lg"),
    *,
    service: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_dto(
        dto=await service.get_by_slug(slug),
        filter_languages=languages,
    )


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    q: str = Query(min_length=1, max_length=50, default=None),
    page_size: PositiveInt | None = Query(None, alias="psize"),
    page_num: PositiveInt | None = Query(None, alias="pnum"),
    date_from: datetime.date | None = Query(None),
    date_to: datetime.date | None = Query(None),
    order: Order = Order.ASC,
    tags: list[Annotated[str, MinLen(2), MaxLen(50)]] = Query(None, alias="tag"),
    tag_param: TagParam | None = None,
    *,
    service: FromDishka[ComicReader],
) -> ComicsWMetadata:
    limit = Limit(page_size) if page_size else None
    offset = Offset(limit * (page_num - 1)) if limit and page_num else None

    total, comic_resp_dtos = await service.get_list(
        ComicFilterParams(
            q=q,
            limit=limit,
            offset=offset,
            order=order,
            date_range=DateRange(start=date_from, end=date_to),
            tags=[TagName(tag) for tag in tags] if tags else [],
            tag_param=tag_param,
        ),
    )

    return ComicsWMetadata(
        meta=PaginationSchema(total=total, limit=limit, offset=offset),
        data=[ComicResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos],
    )


@router.get(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_translations(
    comic_id: int,
    *,
    service: FromDishka[ComicReader],
) -> list[TranslationWLanguageResponseSchema]:
    dtos = await service.get_translations(ComicID(comic_id))
    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in dtos]
