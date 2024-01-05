from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app import Cleaner, CleanerStub, DbEngineStub
from src.core.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine: AsyncEngine = app.dependency_overrides[DbEngineStub]()

    cleaner: Cleaner = app.dependency_overrides[CleanerStub]()
    await cleaner.run()

    await check_db_connection(engine)

    yield

    await cleaner.stop()

    await engine.dispose()
