from sqlalchemy import Boolean, Column, Date, SmallInteger, String, Table, ForeignKey, Integer, UniqueConstraint, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


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
