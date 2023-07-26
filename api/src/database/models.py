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

    fav_id = Column(SmallInteger, primary_key=True)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id', ondelete='CASCADE'))
    user_id = Column(BigInteger, ForeignKey('users.tg_id', ondelete='CASCADE'))
    created_at = Column(Date, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix__favorite'),
    )


class Comic(Base):
    __tablename__ = 'comics'

    def __create_tsvector_exp(*field_names):
        return f"""to_tsvector('english', {" || ' ' || ".join(field_names)})"""

    comic_id = Column(SmallInteger, primary_key=True)
    title = Column(String, nullable=False)
    image = Column(String, nullable=False)
    comment = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)
    publication_date = Column(String, nullable=False)
    is_specific = Column(Boolean, nullable=False, default=False)
    rus_title = Column(String, nullable=False, default='')
    rus_image = Column(String, nullable=False, default='')
    rus_comment = Column(String, nullable=False, default='')
    rus_transcript = Column(String, nullable=False, default='')

    search_vector = Column(
        TSVectorType,
        Computed(
            __create_tsvector_exp('title', 'comment', 'transcript', 'rus_title', 'rus_comment', 'rus_transcript'),
            persisted=True,
        ),
    )

    favorite_count = column_property(
        select(func.count(Favorite.fav_id))
        .where(Favorite.comic_id == comic_id)
        .scalar_subquery()
        .label('favorite_count'),
    )

    favorites = relationship('Favorite', backref='comic', cascade='all, delete')
    explanation = relationship('Explanation', backref='comic', cascade='all, delete')

    @declared_attr
    def total_count(cls):
        return select(func.count(cls.comic_id))

    __table_args__ = (
        Index('ix__comics___ts_vector__', search_vector, postgresql_using='gin'),
        UniqueConstraint('title', 'image', 'comment', name='uix__comics'),
    )

    def to_dto(self):
        return dto.Comic(
            comic_id=self.comic_id,
            title=self.title,
            image=self.image,
            comment=self.comment,
            transcript=self.transcript,
            publication_date=self.publication_date,
            is_specific=self.is_specific,
            favorite_count=self.favorite_count,
            rus_title=self.rus_title,
            rus_image=self.rus_image,
            rus_comment=self.rus_comment,
            rus_transcript=self.rus_transcript,
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(comic_id={self.comic_id}, title={self.title})"


class Explanation(Base):
    __tablename__ = 'explanations'

    explanation_id = Column(SmallInteger, primary_key=True)
    text = Column(Text, unique=True)
    translation = Column(Text)
    comic_id = Column(SmallInteger, ForeignKey('comics.comic_id', ondelete='CASCADE'))


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
