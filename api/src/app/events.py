from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app.dependency_stubs import DbEngineDepStub, HttpClientDepStub
from src.app.temp_utils import HttpClient
from src.core.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine: AsyncEngine = app.dependency_overrides[DbEngineDepStub]()
    client: HttpClient = app.dependency_overrides[HttpClientDepStub]()

    await client.close_unused_sessions_periodically()

    await check_db_connection(engine)

    yield

    await client.close_all_sessions()

    await engine.dispose()
