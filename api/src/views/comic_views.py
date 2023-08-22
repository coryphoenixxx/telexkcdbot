from aiohttp import web
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.repositories import ComicsRepo
from src.router import router
from src.schemas import mytypes
from src.schemas.queries import ComicQueryParams
from src.services.comics_service import ComicsService
from src.utils.exceptions import NotFoundError
from src.utils.filters import filter_keys, filter_langs
from src.utils.json_response import ErrorPayload, SuccessPayload, json_response
from src.utils.validators import clean_errors, validate_request_json


@router.get('/api/comics/{comic_id:\\d+}')
async def api_get_comic_by_id(
        request: web.Request,
        session_factory: async_sessionmaker[AsyncSession],
) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    try:
        params = ComicQueryParams(**request.rel_url.query)
    except ValidationError as err:
        errors = clean_errors(err)

        return json_response(
            data=ErrorPayload(detail=errors),
            status=422,
        )

    try:
        comic_dto = await ComicsService(ComicsRepo(session_factory)).get_comic_by_id(comic_id)
    except NotFoundError:
        return json_response(
            data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    fields = params.fields.split(',') if params.fields else None
    languages = params.languages.split(',') if params.languages else None

    response_data = filter_keys(
        filter_langs(comic_dto.to_dict(), languages),
        fields,
    )

    return json_response(
        data=SuccessPayload(data=response_data),
        status=200,
    )


# @router.get('/api/comics')
# @validate_queries(validator=ComicsQueryParams)
# async def api_get_comic_list(
#         _: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         language: types.LanguageCode,
#         fields: str | None,
#         limit: int | None,
#         offset: int | None,
#         order: types.OrderType | None,
# ) -> web.Response:
#     comic_repo = ComicsRepository(session_factory)
#     comic_dto_list, total = await comic_repo.get_list(limit, offset, order)
#
#     response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]
#
#     return json_response(
#         data=SuccessPayloadWithMeta(
#             meta=Meta(
#                 limit=limit,
#                 offset=offset,
#                 count=len(comic_dto_list),
#                 total=total,
#             ),
#             data=response_data),
#         status=200,
#     )
#
#
# @router.get('/api/comics/search')
# @validate_queries(validator=ComicsSearchQueryParams)
# async def api_search_comics(
#         _: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         language: types.LanguageCode,
#         fields: str | None,
#         limit: int | None,
#         offset: int | None,
#         q: str,
# ) -> web.Response:
#     comic_repo = ComicsRepository(session_factory)
#     comic_dto_list, total = await comic_repo.search(q, limit, offset)
#
#     response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]
#
#     return json_response(
#         data=SuccessPayloadWithMeta(
#             meta=Meta(
#                 limit=limit,
#                 offset=offset,
#                 count=len(comic_dto_list),
#                 total=total,
#             ),
#             data=response_data),
#         status=200,
#     )


@router.post('/api/comics')
@validate_request_json(validator=mytypes.PostComic)
async def api_post_comic(
        _: web.Request,
        session_factory: async_sessionmaker[AsyncSession],
        comic_data: mytypes.PostComic,
) -> web.Response:
    comic_dto = comic_data.to_dto()
    try:
        comic_dto = await ComicsService(ComicsRepo(session_factory)).create_comic(comic_dto)
    except IntegrityError:
        return json_response(
            data=ErrorPayload(detail=[{'reason': "A comic with the same id, title and comment already exists."}]),
            status=409,
        )

    return json_response(
        data=SuccessPayload(data=comic_dto.to_dict()),
        status=201,
    )
#
#
# @router.put('/api/comics/{comic_id:\\d+}')
# @validate_request_json(validator=types.PutComic)
# async def api_put_comic(
#         request: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         new_comic_data: types.PutComic,
# ) -> web.Response:
#     comic_id = int(request.match_info['comic_id'])
#
#     comic_repo = ComicsRepository(session_factory)
#
#     try:
#         comic_data = await comic_repo.update(comic_id, new_comic_data)
#     except IntegrityError:
#         return json_response(
#             data=ErrorPayload(detail=[{'reason': "A comic with the same id, title and comment already exists."}]),
#             status=409,
#         )
#
#     if not comic_data:
#         return json_response(
#             data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
#             status=404,
#         )
#
#     return json_response(
#         data=SuccessPayload(data=comic_data.model_dump()),
#         status=200,
#     )
#
#
# @router.delete('/api/comics/{comic_id:\\d+}')
# async def api_delete_comic(request: web.Request, session_factory: async_sessionmaker[AsyncSession] ):
#     comic_id = int(request.match_info['comic_id'])
#
#     comic_repo = ComicsRepository(session_factory)
#     del_comic_id = await comic_repo.delete(comic_id)
#
#     if not del_comic_id:
#         return json_response(
#             data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
#             status=404,
#         )
#
#     return json_response(status=204)
