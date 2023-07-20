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
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship
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
        return tuple(c for c in cls.__table__.columns if not c.name.endswith('_'))

    @classmethod
    @property
    @functools.cache
    def column_names(cls) -> tuple[str]:
        return tuple(c.name for c in cls.columns)

    def __repr__(self):
        values = [f"{name!r}={getattr(self, name)!r}" for name in self.column_names]
        return f"{self.__class__.__name__!r}({', '.join(values)!r})"


class Comic(Base):
    __tablename__ = 'comics'

    def __create_tsvector_exp(*field_names):
        return f"""to_tsvector('english', {" || ' ' || ".join(field_names)})"""

    comic_id = Column(SmallInteger, primary_key=True)
    title = Column(String, nullable=False)
    image = Column(String, nullable=False)
    comment = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)
    rus_title = Column(String, nullable=False, default='')
    rus_image = Column(String, nullable=False, default='')
    rus_comment = Column(String, nullable=False, default='')
    rus_transcript = Column(String, nullable=False, default='')
    publication_date = Column(String, nullable=False)
    is_specific = Column(Boolean, nullable=False, default=False)
    search_vector_ = Column(
        TSVectorType,
        Computed(
            __create_tsvector_exp('title', 'comment', 'transcript', 'rus_title', 'rus_comment', 'rus_transcript'),
            persisted=True,
        ),
    )

    favorites = relationship('Favorite', backref='comic', cascade='all,delete')
    explanation = relationship('Explanation', backref='comic', uselist=False, lazy=True, cascade='all,delete')

    __table_args__ = (
        Index('ix__comics___ts_vector__', search_vector_, postgresql_using='gin'),
        UniqueConstraint('title', 'image', 'comment', name='uix__comics'),
    )


class Explanation(Base):
    __tablename__ = 'explanations'

    explanation_id = Column(SmallInteger, primary_key=True)
    text = Column(Text, unique=True)
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

    favorites = relationship('Favorite', backref='user', cascade='all,delete')


class Favorite(Base):
    __tablename__ = 'favorites'

    fav_id = Column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix__favorite'),
    )


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    wh_id = Column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix__watch_history'),
    )
