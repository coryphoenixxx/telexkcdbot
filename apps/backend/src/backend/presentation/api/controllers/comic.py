import datetime

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query
from starlette import status

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
    TagNotFoundError,
)
from backend.application.comic.filters import ComicFilters, DateRange, TagCombination
from backend.application.comic.services import (
    ComicReader,
    CreateComicInteractor,
    DeleteComicInteractor,
    UpdateComicInteractor,
)
from backend.application.common.exceptions import TempFileNotFoundError
from backend.application.common.pagination import (
    Pagination,
    SortOrder,
)
from backend.application.image.exceptions import ImageAlreadyHasOwnerError, ImageNotFoundError
from backend.domain.entities import TranslationStatus
from backend.domain.value_objects import ComicId, IssueNumber, Language, TagName
from backend.domain.value_objects.translation_title import TranslationTitleLengthError
from backend.presentation.api.controllers.schemas import (
    ComicCreateSchema,
    ComicResponseSchema,
    ComicsWPaginationSchema,
    ComicWTranslationsResponseSchema,
    PaginationSchema,
    TranslationResponseSchema,
)
from backend.presentation.api.controllers.schemas.requests import ComicUpdateSchema
from backend.presentation.api.controllers.schemas.responses import ComicCompactResponseSchema

router = APIRouter(tags=["Comics"], route_class=DishkaRoute)


@router.post(
    "/comics",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": TranslationTitleLengthError},
        status.HTTP_404_NOT_FOUND: {
            "model": TempFileNotFoundError | TagNotFoundError | ImageNotFoundError
        },
        status.HTTP_409_CONFLICT: {
            "model": ComicNumberAlreadyExistsError
            | ExtraComicTitleAlreadyExistsError
            | ImageAlreadyHasOwnerError
        },
    },
)
async def create_comic(
    schema: ComicCreateSchema,
    *,
    interactor: FromDishka[CreateComicInteractor],
    reader: FromDishka[ComicReader],
) -> ComicResponseSchema:
    comic_id = await interactor.execute(schema.to_command())
    return ComicResponseSchema.from_data(data=await reader.get_by_id(comic_id))


@router.patch(
    "/comics/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ComicNotFoundError
            | TempFileNotFoundError
            | TagNotFoundError
            | ImageNotFoundError
        },
        status.HTTP_409_CONFLICT: {"model": ComicNumberAlreadyExistsError},
    },
)
async def update_comic(
    comic_id: int,
    schema: ComicUpdateSchema,
    *,
    interactor: FromDishka[UpdateComicInteractor],
    reader: FromDishka[ComicReader],
) -> ComicResponseSchema:
    await interactor.execute(schema.to_command(comic_id))
    return ComicResponseSchema.from_data(data=await reader.get_by_id(ComicId(comic_id)))


@router.delete(
    "/comics/id:{comic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def delete_comic(
    comic_id: int,
    *,
    interactor: FromDishka[DeleteComicInteractor],
) -> None:
    await interactor.execute(comic_id=ComicId(comic_id))


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
    reader: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_data(data=await reader.get_by_id(ComicId(comic_id)))


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
    reader: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_data(data=await reader.get_by_issue_number(IssueNumber(number)))


@router.get(
    "/comics/{slug:str}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_extra_comic_by_slug(
    slug: str,
    *,
    reader: FromDishka[ComicReader],
) -> ComicResponseSchema:
    return ComicResponseSchema.from_data(data=await reader.get_by_slug(slug))


@router.get(
    "/comics-with-translations/id:{comic_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_with_translations_by_id(
    comic_id: int,
    *,
    reader: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_data(
        data=await reader.get_by_id(ComicId(comic_id)),
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
    *,
    reader: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_data(
        data=await reader.get_by_issue_number(IssueNumber(number)),
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
    *,
    reader: FromDishka[ComicReader],
) -> ComicWTranslationsResponseSchema:
    return ComicWTranslationsResponseSchema.from_data(data=await reader.get_by_slug(slug))


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
    search_query: str | None = Query(default=None, alias="q"),
    search_language: Language = Query(default=Language.EN, alias="qlg"),
    date_from: datetime.date | None = Query(default=None),
    date_to: datetime.date | None = Query(default=None),
    tags: list[str] = Query(default_factory=list, alias="tag"),
    tag_combination: TagCombination = Query(default=TagCombination.AND, alias="tag_mode"),
    page_size: int = Query(default=100, ge=1, alias="psize"),
    page_num: int = Query(default=1, ge=1, alias="pnum"),
    order: SortOrder = Query(default=SortOrder.ASC),
    *,
    reader: FromDishka[ComicReader],
) -> ComicsWPaginationSchema:
    limit = page_size if page_size else None
    offset = limit * (page_num - 1) if (limit and page_num) else None

    total, comic_datas = await reader.get_list(
        ComicFilters(
            search_query=search_query,
            search_language=Language(search_language),
            date_range=DateRange(start=date_from, end=date_to),
            tag_slugs=[TagName(tag).slug for tag in tags],
            tag_combination=tag_combination,
        ),
        Pagination(limit=limit, offset=offset, order=order),
    )

    return ComicsWPaginationSchema(
        meta=PaginationSchema(total=total, limit=limit, offset=offset),
        data=[ComicCompactResponseSchema.from_data(data=data) for data in comic_datas],
    )


@router.get(
    "/comics/id:{comic_id}/translations",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_translations(
    comic_id: int,
    filter_language: Language | None = Query(default=None, alias="lg"),
    publication_status: TranslationStatus | None = Query(default=None, alias="status"),
    *,
    reader: FromDishka[ComicReader],
) -> list[TranslationResponseSchema]:
    datas = await reader.get_translations(ComicId(comic_id), publication_status, filter_language)
    return [TranslationResponseSchema.from_data(data) for data in datas]
