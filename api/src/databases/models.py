from typing import Optional

from sqlalchemy import Boolean, Column, Date, SmallInteger, String, ForeignKey, Integer, Text, Computed, Index, func, \
    BigInteger, select, and_
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime

from sqlalchemy_utils import TSVectorType


class Base(DeclarativeBase):
    _additional_column_names = None

    @classmethod
    def get_columns(cls, fields: Optional[str] = None):
        columns = [c for c in cls.__table__.columns if not c.name.startswith('_')]
        if fields:
            return [c for c in columns if c.name in fields]
        return columns

    @classmethod
    def get_all_column_names(cls):
        column_names = [c.name for c in cls.get_columns()]
        if cls._additional_column_names:
            column_names.extend(cls._additional_column_names)
        return column_names

    @classmethod
    def get_model_by_tablename(cls, tablename):
        """Return model class reference mapped to table.

        :param tablename: String with name of table.
        :return: Model class reference or None.
        """
        table_name_to_class = {m.tables[0].name: m.class_ for m in Base.registry.mappers}
        return table_name_to_class.get(tablename)


class Comic(Base):
    __tablename__ = 'comics'
    _additional_column_names = ('bookmarked_count', 'bookmarked_by_user')

    comic_id = Column(SmallInteger, primary_key=True)
    title = Column(String, nullable=False)
    image = Column(String, nullable=False)
    comment = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)
    rus_title = Column(String, nullable=True)
    rus_image = Column(String, nullable=True)
    rus_comment = Column(String, nullable=True)
    publication_date = Column(String, nullable=False)
    is_specific = Column(Boolean, nullable=False)
    bookmarks = relationship('Bookmark', backref='comic')
    _ts_vector = Column(
        TSVectorType(),
        Computed(
            "to_tsvector('english', title || ' ' || comment || ' ' || rus_title || ' ' || rus_comment)",
            persisted=True
        )
    )

    @classmethod
    def bookmarked_by_user(cls, user_id: int, comic_id: int):
        return select((func.count('*') > 0)) \
            .select_from(Bookmark) \
            .where(and_(Bookmark.user_id == user_id, Bookmark.comic_id == comic_id)) \
            .scalar_subquery()

    __table_args__ = (
        Index('ix__comics___ts_vector__', _ts_vector, postgresql_using='gin'),
    )


class Explanation(Base):
    __tablename__ = 'explanation'

    _pk = Column(SmallInteger, primary_key=True)
    text = Column(Text)
    translation = Column(Text)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))


class User(Base):
    __tablename__ = 'users'

    tg_id = Column(BigInteger, primary_key=True)
    tg_lang_code = Column(SmallInteger)
    ui_lang = Column(String)
    rus_only_mode = Column(Boolean)
    joined_at = Column(Date, default=datetime.utcnow)
    last_activity_at = Column(Date)
    bookmarks = relationship('Bookmark')


class Bookmark(Base):
    __tablename__ = 'bookmarks'

    _pk = Column(Integer, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    _pk = Column(Integer, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)
