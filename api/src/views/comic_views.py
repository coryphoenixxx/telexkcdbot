from aiohttp import web
from src.database.repositories import ComicRepo
from src.router import router
from src.utils.json_response import ErrorJSONData, SuccessJSONData, json_response
from src.utils.validators import (
    ComicJSONSchema,
    ComicQueryParams,
    ComicsQueryParams,
    ComicsSearchQueryParams,
    validate_post_json,
    validate_queries,
)


@router.get('/api/comics/{comic_id:\\d+}')
@validate_queries(validator=ComicQueryParams)
async def api_get_comic_by_id(request: web.Request, valid_query_params: dict) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    row = await ComicRepo.get_by_id(comic_id, **valid_query_params)

    if not row:
        return json_response(
            data=ErrorJSONData(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
            status=404,
        )

    return json_response(
        data=SuccessJSONData(data=row),
        status=200,
    )


@router.get('/api/comics')
@validate_queries(validator=ComicsQueryParams)
async def api_get_comic_list(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicRepo.get_list(**valid_query_params)

    return json_response(
        data=meta | SuccessJSONData(data=rows),
        status=200,
    )


@router.get('/api/comics/search')
@validate_queries(validator=ComicsSearchQueryParams)
async def api_search_comics(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicRepo.search(**valid_query_params)

    return json_response(
        data=meta | SuccessJSONData(data=rows),
        status=200,
    )


@router.get('/api/comics/{comic_id:\\d+}/favorites-count')
async def api_get_comic_favorites_count(request: web.Request) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    favorites_count = await ComicRepo.get_favorites_count(comic_id)

    return json_response(
        data=SuccessJSONData(data={
            "comic_id": comic_id,
            "favorites_count": favorites_count,
        }),
        status=200,
    )


@router.post('/api/comics')
@validate_post_json(validator=ComicJSONSchema)
async def api_post_comics(request: web.Request, comic_data_list: list[dict]) -> web.Response:
    await ComicRepo.add(comic_data_list)

    return json_response(
        data=SuccessJSONData(data=comic_data_list),
        status=201,
    )
