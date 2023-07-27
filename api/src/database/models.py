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
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, column_property, declared_attr, relationship
from sqlalchemy_utils import TSVectorType
from src.database import dto


class Base(DeclarativeBase):
    ...


class Favorite(Base):
    __tablename__ = 'favorites'

    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.tg_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(Date, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix__favorite'),
    )


class ComicTranslation(Base):
    __tablename__ = 'comic_translations'

    def __create_tsvector_exp(*field_names):
        return f"""to_tsvector('english', {" || ' ' || ".join(field_names)})"""

    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id', ondelete='CASCADE'), primary_key=True)
    language_code = Column(String(2), nullable=False, primary_key=True)
    title = Column(String, nullable=False)
    comment = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)

    search_vector = Column(
        TSVectorType,
        Computed(
            __create_tsvector_exp('title', 'comment', 'transcript'),
            persisted=True,
        ),
    )

    __table_args__ = (
        Index('ix__comics___ts_vector__', search_vector, postgresql_using='gin'),
        UniqueConstraint('title', 'image_url', 'comment', name='uix__comics'),
    )

    def to_dto(self):
        return dto.ComicTranslation(
            language_code=self.language_code,
            title=self.title,
            image_url=self.image_url,
            comment=self.comment,
            transcript=self.transcript,
        )


class Comic(Base):
    __tablename__ = 'comics'

    comic_id = Column(SmallInteger, primary_key=True)
    publication_date = Column(String, nullable=False)
    is_specific = Column(Boolean, nullable=False, default=False)

    favorite_count = column_property(
        select(func.count('*'))
        .where(Favorite.comic_id == comic_id)
        .correlate_except(Favorite)
        .scalar_subquery(),
    )

    translations = relationship('ComicTranslation', cascade='all, delete', uselist=True)
    favorites = relationship('Favorite', backref='comic', cascade='all, delete')
    explanation = relationship('Explanation', backref='comic', cascade='all, delete')

    @declared_attr
    def total_count(cls):
        return select(func.count(cls.comic_id))

    def to_dto(self):
        translations = {}

        for tr in self.translations:
            translations.update(tr.to_dto().as_dict())

        return dto.Comic(
            comic_id=self.comic_id,
            is_specific=self.is_specific,
            favorite_count=self.favorite_count,
            publication_date=self.publication_date,
            translations=translations,
        )


class Explanation(Base):
    __tablename__ = 'explanations'

    exp_id = Column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id', ondelete='CASCADE'))


class ExplanationTranslations(Base):
    __tablename__ = 'explanation_translations'

    exp_id = Column(SmallInteger, ForeignKey('explanations.exp_id', ondelete='CASCADE'), primary_key=True)
    language_code = Column(String(2), nullable=False, primary_key=True)
    text = Column(Text)


class User(Base):
    __tablename__ = 'users'

    tg_id = Column(BigInteger, primary_key=True)
    tg_lang_code = Column(SmallInteger)
    ui_lang = Column(String)
    rus_only_mode = Column(Boolean)
    joined_at = Column(Date, default=datetime.utcnow)
    last_activity_at = Column(Date)

    favorites = relationship('Favorite', backref='user', cascade='all, delete')


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    wh_id = Column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))
    created_at = Column(Date, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix__watch_history'),
    )
