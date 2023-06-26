from sqlalchemy import select
from aiohttp import web
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError

from src.databases.base import db_pool
from src.databases.models import Comic

from dataclasses import dataclass, asdict

router = web.RouteTableDef()


@dataclass
class SuccessJSONData:
    data: dict | list
    status: str = "success"
    message: str = None


@dataclass
class ErrorJSONData:
    message: str
    status: str = "error"
    data: dict | list = None


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
            stmt = select(Comic).where(Comic.comic_id == int(comic_id))
            result = (await session.execute(stmt)).scalar()
        await session.commit()

    if not result:
        return web.json_response(
            data=asdict(ErrorJSONData(message=f"Comic {comic_id} doesn't exists.")),
            status=404
        )

    comic_data = {}
    if fields:
        for field in fields.split(','):
            try:
                comic_data[field] = getattr(result, field)
            except AttributeError:
                return web.json_response(
                    data=asdict(ErrorJSONData(message=f"Invalid field({field}) value.")),
                    status=400
                )
    else:
        for field in Comic.__dict__.keys():
            if not field.startswith('_'):
                comic_data[field] = getattr(result, field)

    return web.json_response(
        data=asdict(SuccessJSONData(data=comic_data)),
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
                    data=asdict(ErrorJSONData(message="Invalid data types or json structure.")),
                    status=400
                )

    return web.json_response(
        data=asdict(SuccessJSONData(data=comic_data_list)),
        status=201
    )
