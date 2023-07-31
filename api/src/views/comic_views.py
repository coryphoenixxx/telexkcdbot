from aiohttp import web
from sqlalchemy.exc import IntegrityError
from src import types
from src.database.repositories import ComicRepository
from src.router import router
from src.utils.json_response import ErrorPayload, Meta, SuccessPayload, SuccessPayloadWithMeta, json_response
from src.utils.validators import (
    ComicQueryParams,
    ComicsQueryParams,
    ComicsSearchQueryParams,
    validate_queries,
    validate_request_json,
)


@router.get('/api/comics/{comic_id:\\d+}')
@validate_queries(validator=ComicQueryParams)
async def api_get_comic_by_id(
        request: web.Request,
        language: types.LanguageCode | None,
        fields: str | None,
) -> web.Response:

    comic_id = int(request.match_info['comic_id'])

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_dto = await comic_repo.get_by_id(comic_id)

    if not comic_dto:
        return json_response(
            data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    response_data = comic_dto.filter(language, fields)

    return json_response(
        data=SuccessPayload(data=response_data),
        status=200,
    )


@router.get('/api/comics')
@validate_queries(validator=ComicsQueryParams)
async def api_get_comic_list(
        request: web.Request,
        language: types.LanguageCode,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        order: types.OrderType | None,
) -> web.Response:

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_dto_list, total = await comic_repo.get_list(limit, offset, order)

    response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]

    return json_response(
        data=SuccessPayloadWithMeta(
            meta=Meta(
                limit=limit,
                offset=offset,
                count=len(comic_dto_list),
                total=total,
            ),
            data=response_data),
        status=200,
    )


@router.get('/api/comics/search')
@validate_queries(validator=ComicsSearchQueryParams)
async def api_search_comics(
        request: web.Request,
        language: types.LanguageCode,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        q: str,
) -> web.Response:

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_dto_list, total = await comic_repo.search(q, limit, offset)

    response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]

    return json_response(
        data=SuccessPayloadWithMeta(
            meta=Meta(
                limit=limit,
                offset=offset,
                count=len(comic_dto_list),
                total=total,
            ),
            data=response_data),
        status=200,
    )


@router.post('/api/comics')
@validate_request_json(validator=types.PostComic)
async def api_post_comics(request: web.Request, comic_data: types.PostComic) -> web.Response:

    comic_repo = ComicRepository(session_factory=request.app.session_factory)

    try:
        comic_dto = await comic_repo.create(comic_data)
    except IntegrityError:
        return json_response(
            data=ErrorPayload(detail=[{'reason': "A comic with the same id, title and comment already exists."}]),
            status=409,
        )

    return json_response(
        data=SuccessPayload(data=comic_dto.model_dump()),
        status=201,
    )


@router.put('/api/comics/{comic_id:\\d+}')
@validate_request_json(validator=types.PutComic)
async def api_put_comic(request: web.Request, new_comic_data: types.PutComic) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    comic_repo = ComicRepository(session_factory=request.app.session_factory)

    try:
        comic_data = await comic_repo.update(comic_id, new_comic_data)
    except IntegrityError:
        return json_response(
            data=ErrorPayload(detail=[{'reason': "A comic with the same id, title and comment already exists."}]),
            status=409,
        )

    if not comic_data:
        return json_response(
            data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    return json_response(
        data=SuccessPayload(data=comic_data.model_dump()),
        status=200,
    )


@router.delete('/api/comics/{comic_id:\\d+}')
async def api_delete_comic(request: web.Request):
    comic_id = int(request.match_info['comic_id'])

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    del_comic_id = await comic_repo.delete(comic_id)

    if not del_comic_id:
        return json_response(
            data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    return json_response(status=204)
