from aiohttp import web
from src.database.comic_db import ComicDB
from src.utils.json_response_dataclasses import ErrorJSONData, SuccessJSONData
from src.utils.validators import comic_json_schema, validate_json, validate_queries


@validate_queries
async def api_get_comic(request: web.Request, valid_query_params: dict) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    row = await ComicDB.get_comic_detail(comic_id, valid_query_params)

    if not row:
        return web.json_response(
            data=ErrorJSONData(message=f"Comic {comic_id} doesn't exists.").to_dict(),
            status=404,
        )

    return web.json_response(
        data=SuccessJSONData(data=dict(row._mapping)).to_dict(),
        status=200,
    )


@validate_queries
async def api_get_found_comics(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicDB.get_found_comic_list(valid_query_params)

    return web.json_response(
        data=meta | SuccessJSONData(data=[dict(row._mapping) for row in rows]).to_dict(),
        status=200,
    )


@validate_queries
async def api_get_comics(request: web.Request, valid_query_params: dict) -> web.Response:
    rows, meta = await ComicDB.get_comic_list(valid_query_params)

    # TODO: if not rows

    return web.json_response(
        data=meta | SuccessJSONData(data=[dict(row._mapping) for row in rows]).to_dict(),
        status=200,
    )


@validate_json(comic_json_schema)
async def api_post_comics(request: web.Request, comic_data_list: dict) -> web.Response:
    await ComicDB.add_comics(comic_data_list)

    return web.json_response(
        data=SuccessJSONData(data=comic_data_list).to_dict(),
        status=201,
    )
