from collections.abc import Callable
from json import JSONDecodeError

from aiohttp import web
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.helpers.exceptions import CustomError
from src.helpers.json_response import json_error_response


def db_session_middleware_factory(session_factory: async_sessionmaker[AsyncSession]):
    @web.middleware
    async def db_session_middleware(request: web.Request, handler: Callable):
        response = await handler(request, session_factory)  # TODO: root handler?
        return response

    return db_session_middleware


# TODO:
@web.middleware
async def error_middleware(request: web.Request, handler: Callable):
    try:
        return await handler(request)
    except ValidationError as err:
        return json_error_response(detail=err, code=422)
    except JSONDecodeError:
        return json_error_response(reason="Invalid JSON format.")
    except CustomError as err:
        return json_error_response(reason=str(err))
