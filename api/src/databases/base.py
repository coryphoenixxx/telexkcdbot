from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api_config import DATABASE_URL
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(DATABASE_URL, future=True, echo=True)

db_pool = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    additional_column_names = None

    @classmethod
    def get_columns(cls, fields: Optional[str] = None):
        columns = [c for c in cls.__table__.columns if not c.name.startswith('_')]
        if fields:
            return [c for c in columns if c.name in fields]
        return columns

    @classmethod
    def get_all_column_names(cls):
        column_names = [c.name for c in cls.get_columns()]
        if cls.additional_column_names:
            column_names.extend(cls.additional_column_names)
        return column_names

    @classmethod
    def get_model_by_tablename(cls, table_name):
        """Return model class reference mapped to table.

        :param table_name: String with name of table.
        :return: Model class reference or None.
        """
        table_name_to_class = {m.tables[0].name: m.class_ for m in Base.registry.mappers}
        return table_name_to_class.get(table_name)
