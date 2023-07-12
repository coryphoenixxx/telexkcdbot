from aiohttp import web
from src.database.comic_db import ComicDb
from src.utils.json_response import ErrorJSONData, SuccessJSONData, json_response
from src.utils.validators import comic_json_schema, validate_json, validate_queries
from src.views.router import Router


@Router.routes.get('/api/comics/{comic_id:\\d+}')
@validate_queries
async def api_get_comic(request: web.Request, valid_query_params: dict) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    row = await ComicDb.get_comic_detail(comic_id, **valid_query_params)

    if not row:
        return json_response(
            data=ErrorJSONData(message=f"Comic {comic_id} doesn't exists."),
            status=404,
        )

    return json_response(
        data=SuccessJSONData(data=row),
        status=200,
    )


@Router.routes.get('/api/comics')
@validate_queries
async def api_get_comics(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicDb.get_comic_list(**valid_query_params)

    # TODO: if not rows

    return json_response(
        data=meta | SuccessJSONData(data=rows),
        status=200,
    )


@Router.routes.get('/api/comics/search')
@validate_queries
async def api_get_found_comics(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicDb.get_found_comic_list(**valid_query_params)

    return json_response(
        data=meta | SuccessJSONData(data=rows),
        status=200,
    )


@Router.routes.post('/api/comics')
@validate_json(comic_json_schema)
async def api_post_comics(request: web.Request, comic_data_list: list[dict]) -> web.Response:
    await ComicDb.add_comics(comic_data_list)

    return json_response(
        data=SuccessJSONData(data=comic_data_list),
        status=201,
    )
