from sqlalchemy import Boolean, Column, Date, SmallInteger, String, ForeignKey, Integer, Text, Computed, Index, func, \
    BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from sqlalchemy_utils import TSVectorType, aggregated

from src.databases.base import Base


class Comic(Base):
    __tablename__ = 'comics'
    additional_column_names = ('bookmarked_count', 'bookmarked_by_user')

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
