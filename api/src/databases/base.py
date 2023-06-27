from pprint import pprint
from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api_config import DATABASE_URL
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(DATABASE_URL, future=True, echo=True)

db_pool = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    @classmethod
    def get_columns(cls, col_names: Optional[tuple] = None):
        if col_names:
            if not cls.validate_fields(col_names):
                raise AttributeError('Incorrect column name')
            else:
                return (col for col in cls.__table__.columns if col.name in col_names)

        return cls.__table__.columns

    @classmethod
    def validate_fields(cls, col_names: tuple):
        table_columns_names_set = {c.name for c in cls.__table__.columns}
        return set(col_names) <= table_columns_names_set
