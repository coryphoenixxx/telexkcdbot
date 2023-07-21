from aiohttp import web
from sqlalchemy.exc import IntegrityError
from src.database.repositories import ComicRepository
from src.router import router
from src.utils.json_response import ErrorJSONData, SuccessJSONData, SuccessJSONDataWithMeta, json_response
from src.utils.validators import (
    ComicJSONSchema,
    ComicQueryParams,
    ComicsQueryParams,
    ComicsSearchQueryParams,
    validate_post_json,
    validate_queries,
)


def filter_fields(model_data: dict, fields: str | None):
    if fields:
        return {k: v for (k, v) in model_data.items() if k in fields.split(',')}
    return model_data


@router.get('/api/comics/{comic_id:\\d+}')
@validate_queries(validator=ComicQueryParams)
async def api_get_comic_by_id(request: web.Request, fields: str | None) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_data = await comic_repo.get_by_id(comic_id)

    if not comic_data:
        return json_response(
            data=ErrorJSONData(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    data = filter_fields(comic_data, fields)

    return json_response(
        data=SuccessJSONData(data=data),
        status=200,
    )


@router.get('/api/comics')
@validate_queries(validator=ComicsQueryParams)
async def api_get_comic_list(
        request: web.Request,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        order: int | None,
) -> web.Response:
    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_list, total = await comic_repo.get_list(limit, offset, order)

    meta = {
        'limit': limit,
        'offset': offset,
        'count': len(comic_list),
        'total': total,
    }

    data = [filter_fields(comic_data, fields) for comic_data in comic_list]

    return json_response(
        data=SuccessJSONDataWithMeta(meta=meta, data=data),
        status=200,
    )


@router.get('/api/comics/search')
@validate_queries(validator=ComicsSearchQueryParams)
async def api_search_comics(
        request: web.Request,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        q: str | None,
) -> web.Response:
    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    comic_list, total = await comic_repo.search(q, limit, offset)

    meta = {
        'limit': limit,
        'offset': offset,
        'count': len(comic_list),
        'total': total,
    }

    data = [filter_fields(comic_data, fields) for comic_data in comic_list]

    return json_response(
        data=SuccessJSONDataWithMeta(meta=meta, data=data),
        status=200,
    )


@router.get('/api/comics/{comic_id:\\d+}/favorites-count')
async def api_get_comic_favorite_count(request: web.Request) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    comic_repo = ComicRepository(session_factory=request.app.session_factory)
    favorites_count = await comic_repo.get_favorite_count(comic_id)

    return json_response(
        data=SuccessJSONData(data={
            "comic_id": comic_id,
            "favorites_count": favorites_count,
        }),
        status=200,
    )


@router.post('/api/comics')
@validate_post_json(validator=ComicJSONSchema)
async def api_post_comics(request: web.Request, comic_data: list[dict] | dict) -> web.Response:
    comic_repo = ComicRepository(session_factory=request.app.session_factory)

    try:
        comic_id = await comic_repo.add(comic_data)
    except IntegrityError:
        return json_response(
            data=ErrorJSONData(detail=[{'reason': "A comic with the same id or title already exists."}]),
            status=409,
        )

    return json_response(
        data=SuccessJSONData(data={'comic_id': comic_id}),
        status=201,
    )
