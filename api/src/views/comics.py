from pprint import pprint

from sqlalchemy import select, func, case
from aiohttp import web
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError

from src.databases.base import db_pool
from src.databases.models import Comic, Bookmark
from src.utils.json_data import ErrorJSONData, SuccessJSONData

router = web.RouteTableDef()


@router.get("/api")
async def api_handler(request: web.Request) -> web.Response:
    # TODO: отдавать список доступных роутов
    return web.json_response(
        data={"status": "OK"},
        status=200
    )


@router.get('/api/comics/{comic_id:\d+}')
async def api_get_comic(request: web.Request) -> web.Response:
    comic_id: str = request.match_info['comic_id']
    fields_param: str = request.rel_url.query.get('fields')

    fields = tuple(fields_param.split(',')) if fields_param else ()

    if not Comic.validate_fields(fields):
        return web.json_response(
            data=ErrorJSONData(message=f"Invalid fields query parameter.").to_dict(),
            status=400
        )

    async with db_pool() as session:
        async with session.begin():
            stmt = select(*Comic.get_columns(fields), func.count(Bookmark.comic_id).label('bookmarked_count')) \
                .outerjoin(Bookmark) \
                .where(Comic.comic_id == int(comic_id)) \
                .group_by(Comic.comic_id)

            row = (await session.execute(stmt)).fetchone()
        await session.commit()

    if not row:
        return web.json_response(
            data=ErrorJSONData(message=f"Comic {comic_id} doesn't exists.").to_dict(),
            status=404
        )

    return web.json_response(
        data=SuccessJSONData(data=dict(row._mapping)).to_dict(),
        status=200
    )


@router.get('/api/comics')
async def api_get_comics(request: web.Request) -> web.Response:
    fields_param: str = request.rel_url.query.get('fields')
    q_param: str = request.rel_url.query.get('q')
    limit_param: str = request.rel_url.query.get('limit')


    fields = tuple(fields_param.split(',')) if fields_param else ()

    if not Comic.validate_fields(fields):
        return web.json_response(
            data=ErrorJSONData(message=f"Invalid fields query parameter.").to_dict(),
            status=400
        )

    limit = None
    if limit_param:
        if not limit_param.isdigit():
            return web.json_response(
                data=ErrorJSONData(message=f"Invalid limit query parameter.").to_dict(),
                status=400
            )
        else:
            limit = int(limit_param)

    if not q_param:
        q_param = 'x|!x'

    async with db_pool() as session:
        async with session.begin():
            stmt = select(*Comic.get_columns(fields), func.count(Bookmark.comic_id).label('bookmarked_count')) \
                .outerjoin(Bookmark) \
                .where(Comic._ts_vector.bool_op("@@")(func.to_tsquery(q_param if q_param else 'x|!x'))) \
                .group_by(Comic.comic_id) \
                .limit(limit)
            rows = (await session.execute(stmt)).fetchall()

        await session.commit()

    return web.json_response(
        data=SuccessJSONData(data=[dict(row._mapping) for row in rows]).to_dict(),
        status=200
    )


@router.post('/api/comics')
async def api_post_comics(request: web.Request) -> web.Response:
    comic_data_list = await request.json()

    async with db_pool() as session:
        async with session.begin():
            try:
                await session.execute(
                    insert(Comic).on_conflict_do_nothing(),
                    comic_data_list
                )
                await session.commit()
            except DBAPIError as err:
                await session.rollback()
                return web.json_response(
                    data=ErrorJSONData(message="Invalid data types or json structure.").to_dict(),
                    status=400
                )

    return web.json_response(
        data=SuccessJSONData(data=comic_data_list).to_dict(),
        status=201
    )
