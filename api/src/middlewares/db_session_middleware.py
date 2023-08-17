from collections.abc import Callable

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def db_session_middleware_factory(session_factory: async_sessionmaker[AsyncSession]):
    @web.middleware
    async def db_session_middleware(request: web.Request, handler: Callable):
        response = await handler(request, session_factory)
        return response
    return db_session_middleware
