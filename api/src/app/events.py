from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app import DbEngineDepStub
from src.core.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine: AsyncEngine = app.dependency_overrides[DbEngineDepStub]()

    await check_db_connection(engine)

    yield

    await engine.dispose()
