import functools
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Computed,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import TSVectorType


class Base(DeclarativeBase):
    @classmethod
    def filter_columns(cls, fields: str):
        if fields:
            return [c for c in cls.columns if c.name in fields.split(',')]
        return cls.columns

    @classmethod
    @property
    @functools.cache
    def columns(cls) -> tuple[Column]:
        return tuple(c for c in cls.__table__.columns if not c.name.startswith('_'))

    @classmethod
    @property
    @functools.cache
    def column_names(cls) -> tuple[str]:
        return tuple(c.name for c in cls.columns)

    def __repr__(self):
        values = [f"{name!r}={getattr(self, name)!r}" for name in self.column_names]
        return f"{self.__class__.__name__!r}({', '.join(values)})"


class Comic(Base):
    __tablename__ = 'comics'

    comic_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str] = mapped_column(String, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    rus_title: Mapped[str] = mapped_column(String, nullable=True)
    rus_image: Mapped[str] = mapped_column(String, nullable=True)
    rus_comment: Mapped[str] = mapped_column(String, nullable=True)
    publication_date: Mapped[str] = mapped_column(String, nullable=False)
    is_specific: Mapped[bool] = mapped_column(Boolean, nullable=False)
    _ts_vector = Column(
        TSVectorType(),  # TODO:
        Computed(
            "to_tsvector(" +
            "'english', title || ' ' || comment || ' ' || rus_title || ' ' || rus_comment" +
            ")",
            persisted=True,
        ),
    )

    favorites = relationship('Favorite', backref='comic')
    explanation = relationship('Explanation', backref='comic', uselist=False, lazy=True)

    __table_args__ = (
        Index('ix__comics___ts_vector__', _ts_vector, postgresql_using='gin'),
    )


class Explanation(Base):
    __tablename__ = 'explanations'

    explanation_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
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
    favorites = relationship('Favorite', backref='user')


class Favorite(Base):
    __tablename__ = 'favorites'

    fav_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    wh_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)
