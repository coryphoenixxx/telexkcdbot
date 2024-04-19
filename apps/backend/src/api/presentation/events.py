from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.http_client import AsyncHttpClient
from sqlalchemy.ext.asyncio import AsyncEngine

from api.infrastructure.database import check_db_connection
from api.presentation.router import root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_engine: AsyncEngine = app.dependency_overrides[AsyncEngine]()
    http_client: AsyncHttpClient = app.dependency_overrides[AsyncHttpClient]()

    await check_db_connection(db_engine)

    async with http_client, root_router.lifespan_context(app):
        yield

    await db_engine.dispose()
