from sqlalchemy import select, func
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
async def comic(request: web.Request) -> web.Response:
    comic_id: str = request.match_info['comic_id']
    fields: str = request.rel_url.query.get('fields')

    async with db_pool() as session:
        async with session.begin():
            stmt = select(*Comic.columns, func.count(Bookmark.comic_id)) \
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

    if fields:
        response_data = {}
        for field in fields.split(','):
            try:
                response_data[field] = getattr(row, field)
            except AttributeError:
                return web.json_response(
                    data=ErrorJSONData(message=f"Invalid field ({field}) value.").to_dict(),
                    status=400
                )
    else:
        response_data = dict(row._mapping)

    return web.json_response(
        data=SuccessJSONData(data=response_data).to_dict(),
        status=200
    )


@router.get('/api/comics')
async def comics(request: web.Request) -> web.Response:
    fields: str = request.rel_url.query.get('fields')
    q: str = request.rel_url.query.get('fields')

    return web.json_response(
        {"comics_ids": (0,)},
        status=200
    )


@router.post('/api/comics')
async def add_new_comics(request: web.Request) -> web.Response:
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
