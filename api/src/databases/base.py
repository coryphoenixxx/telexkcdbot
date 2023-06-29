from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api_config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
db_pool = async_sessionmaker(engine, expire_on_commit=False)
