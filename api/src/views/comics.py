from functools import wraps

from sqlalchemy import select, func
from aiohttp import web
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError

from src.databases.base import db_pool
from src.databases.models import Comic, Bookmark, Base
from src.utils.json_data import ErrorJSONData, SuccessJSONData

router = web.RouteTableDef()


class InvalidQueryError(Exception):
    def __init__(self, param, value):
        self.message = f"Invalid {param} ({value}) query parameter."
        super().__init__(self.message)


def validate_queries(handler_func):
    @wraps(handler_func)
    async def wrapped(request: web.Request):
        queries = request.rel_url.query
        fields = queries.get('fields')

        try:
            for param in ('user_id', 'limit', 'offset'):
                value = queries.get(param)
                if value:
                    if not value.lstrip('-').isdigit():
                        raise InvalidQueryError(param, value)

            if fields:
                field_list = fields.split(',')
                resource_ = request.rel_url.raw_parts[2]
                model = Base.get_model_by_tablename(resource_)

                invalid_fields = set(field_list) - set(model.get_all_column_names())
                if invalid_fields:
                    raise InvalidQueryError(param='fields', value=', '.join(invalid_fields))

        except InvalidQueryError as err:
            return web.json_response(
                data=ErrorJSONData(
                    message=err.message
                ).to_dict(),
                status=422
            )

        return await handler_func(request)

    return wrapped


@router.get("/api")
async def api_handler(request: web.Request) -> web.Response:
    # TODO: отдавать список доступных роутов
    return web.json_response(
        data={"status": "OK"},
        status=200
    )


@router.get('/api/comics/{comic_id:\d+}')
@validate_queries
async def api_get_comic(request: web.Request) -> web.Response:
    comic_id: str = request.match_info['comic_id']
    fields: str = request.rel_url.query.get('fields')
    user_id: str = request.rel_url.query.get('user_id')

    selected_columns = Comic.get_columns(fields)
    if not fields or 'bookmarked_count' in fields:
        selected_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))

    group_by_columns = [Comic.comic_id]
    if user_id:
        subquery = Comic.bookmarked_by_user(user_id=int(user_id), comic_id=int(comic_id))
        selected_columns.append(subquery.label('bookmarked_by_user'))

    async with db_pool() as session:
        async with session.begin():
            stmt = select(*selected_columns) \
                .select_from(Comic, Bookmark) \
                .outerjoin(Bookmark) \
                .where(Comic.comic_id == int(comic_id)) \
                .group_by(*group_by_columns)

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

    async with db_pool() as session:
        async with session.begin():
            stmt = select(
                *Comic.get_columns(fields), func.count(Bookmark.comic_id).label('bookmarked_count')
            ).outerjoin(Bookmark)

            if q_param:
                stmt = stmt.where(Comic._ts_vector.bool_op("@@")(func.to_tsquery(q_param)))

            stmt = stmt.group_by(Comic.comic_id).limit(limit)

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
