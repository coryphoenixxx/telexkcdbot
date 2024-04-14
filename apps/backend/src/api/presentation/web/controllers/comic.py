import datetime

from fastapi import Depends
from fastapi.params import Query
from faststream.nats.fastapi import NatsRouter as APIRouter
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
    ImagesAlreadyAttachedError,
    ImagesNotCreatedError,
)
from api.application.services.comic import ComicService
from api.infrastructure.database.holder import DatabaseHolder
from api.infrastructure.database.types import ComicFilterParams, DateRange, Limit, Offset, TagParam
from api.presentation.stub import Stub
from api.presentation.web.controllers.schemas.requests.comic import ComicRequestSchema
from api.presentation.web.controllers.schemas.responses.comic import (
    ComicResponseSchema,
    ComicsWithMetadata,
    ComicWTranslationsResponseSchema,
    Pagination,
)
from api.presentation.web.controllers.schemas.responses.translation import (
    TranslationWLanguageResponseSchema,
)
from api.types import ComicID, IssueNumber, Language, Tag
from shared.types import Order

router = APIRouter(tags=["Comics"])


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
        languages: list[Language] = Query(default=None, alias="lg"),
        *,
        db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_id(comic_id)

    return _build_response_comic_schema_by_params(comic_resp_dto, languages=languages)


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
        languages: list[Language] = Query(default=None, alias="lg"),
        *,
        db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_issue_number(number)

    return _build_response_comic_schema_by_params(comic_resp_dto, languages=languages)


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
        languages: list[Language] = Query(default=None, alias="lg"),
        *,
        db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    comic_resp_dto: ComicResponseWTranslationsDTO = await ComicService(
        db_holder=db_holder,
    ).get_by_slug(slug)

    return _build_response_comic_schema_by_params(comic_resp_dto, languages=languages)


@router.get("/comics", status_code=status.HTTP_200_OK)
async def get_comics(
        page_size: int | None = Query(None, alias="psize"),
        page_num: int | None = Query(None, alias="pnum"),
        date_from: datetime.date | None = Query(None),
        date_to: datetime.date | None = Query(None),
        order: Order = Order.ASC,
        tags: list[Tag] = Query(None, alias="tag"),
        tag_param: TagParam | None = None,
        *,
        db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> ComicsWithMetadata:
    limit = Limit(page_size) if page_num else None
    offset = Offset(limit * (page_num - 1)) if limit and page_num else None

    count, comic_resp_dtos = await ComicService(
        db_holder=db_holder,
    ).get_list(
        ComicFilterParams(
            limit=limit,
            offset=offset,
            order=order,
            date_range=DateRange(start=date_from, end=date_to),
            tags=tags,
            tag_param=tag_param,
        ),
    )

    return ComicsWithMetadata(
        meta=Pagination(
            total=count,
            limit=limit,
            offset=offset,
        ),
        data=[ComicResponseSchema.from_dto(dto=dto) for dto in comic_resp_dtos],
    )


@router.get(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicByIDNotFoundError},
    },
)
async def get_comic_translations(
        comic_id: ComicID,
        is_draft: bool = False,
        *,
        db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> list[TranslationWLanguageResponseSchema]:
    translation_resp_dtos = await ComicService(db_holder).get_translations(comic_id, is_draft)

    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in translation_resp_dtos]


def _build_response_comic_schema_by_params(
        dto: ComicResponseWTranslationsDTO,
        languages: list[Language],
) -> ComicResponseSchema | ComicWTranslationsResponseSchema:
    if languages:
        return ComicWTranslationsResponseSchema.from_dto(
            dto=dto,
            filter_languages=languages,
        )
    return ComicResponseSchema.from_dto(dto=dto)
