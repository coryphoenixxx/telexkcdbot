from sqlalchemy import Boolean, Column, Date, SmallInteger, String, ForeignKey, Integer, Text, \
    TypeDecorator, Computed, Index
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from datetime import datetime
from src.databases.base import Base

from sqlalchemy.dialects.postgresql import TSVECTOR


# class TSVector(TypeDecorator):
#     impl = TSVECTOR
#     cache_ok = True

class TSVector(TypeDecorator):
    impl = TSVECTOR
    cache_ok = True

    class comparator_factory(TSVECTOR.Comparator):
        def match(self, other, **kwargs):
            if 'postgresql_regconfig' not in kwargs:
                if 'regconfig' in self.type.options:
                    kwargs['postgresql_regconfig'] = (
                        self.type.options['regconfig']
                    )
            return TSVECTOR.Comparator.match(self, other, **kwargs)

        def __or__(self, other):
            return self.op('||')(other)

    def __init__(self, *args, **kwargs):
        """
        Initializes new TSVectorType

        :param *args: list of column names
        :param **kwargs: various other options for this TSVectorType
        """
        self.columns = args
        self.options = kwargs
        super().__init__()


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(Date, default=datetime.utcnow)


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(Date, default=datetime.utcnow)


class Comic(Base):
    __tablename__ = "comics"

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

    @hybrid_property
    def book(self):
        return

    @book.expression
    def book(cls):
        return


    _ts_vector = Column(
        TSVector(),
        Computed(
            "to_tsvector('english', title || ' ' || comment || ' ' || rus_title || ' ' || rus_comment)",
            persisted=True
        )
    )

    __table_args__ = (
        Index('ix__comics___ts_vector__', _ts_vector, postgresql_using='gin'),
    )


class Explanation(Base):
    __tablename__ = "explanation"

    id = Column(SmallInteger, primary_key=True)
    text = Column(Text)
    translation = Column(Text)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(SmallInteger)
    tg_lang_code = Column(SmallInteger)
    ui_lang = Column(String)
    rus_only_mode = Column(Boolean)
    joined_at = Column(Date, default=datetime.utcnow)
    bookmarks = relationship(Bookmark)
