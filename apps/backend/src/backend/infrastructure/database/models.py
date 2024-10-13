from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.domain.entities import TranslationStatus


class BaseModel(DeclarativeBase):
    __abstract__ = True


BaseModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class TimestampMixin:
    created_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )


class ImageModel(BaseModel, TimestampMixin):
    __tablename__ = "images"

    image_id: Mapped[int] = mapped_column(primary_key=True)
    temp_image_id: Mapped[UUID | None] = mapped_column()
    link_type: Mapped[str | None] = mapped_column(default=None)
    link_id: Mapped[int | None] = mapped_column(default=None)
    original_path: Mapped[str | None] = mapped_column(default=None)
    converted_path: Mapped[str | None] = mapped_column(default=None)
    x2_path: Mapped[str | None] = mapped_column(default=None)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB)
    position_number: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index(
            "ix_image_link_type_link_id",
            "link_type",
            "link_id",
            postgresql_using="btree",
        ),
    )


class TranslationModel(BaseModel, TimestampMixin):
    __tablename__ = "translations"

    translation_id: Mapped[int] = mapped_column(primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.comic_id", ondelete="CASCADE"))
    title: Mapped[str]
    language: Mapped[str] = mapped_column(String(2))
    tooltip: Mapped[str] = mapped_column(default="")
    transcript: Mapped[str] = mapped_column(default="")
    translator_comment: Mapped[str] = mapped_column(default="")
    source_url: Mapped[str | None]
    status: Mapped[str] = mapped_column(String(20))
    searchable_text: Mapped[str] = mapped_column(Text)

    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    images: Mapped[list["ImageModel"]] = relationship(
        primaryjoin="and_("
        "ImageModel.link_type == 'TRANSLATION',"
        "foreign(ImageModel.link_id) == TranslationModel.translation_id,"
        "ImageModel.is_deleted.is_(false()),"
        ")",
    )

    __table_args__ = (
        Index(
            "uq_translation_if_published",
            "language",
            "comic_id",
            unique=True,
            postgresql_where=(status == TranslationStatus.PUBLISHED),
        ),
        Index(
            "ix_translations_searchable_text",
            "searchable_text",
            postgresql_using="pgroonga",
        ),
    )


class ComicTagAssociation(BaseModel):
    __tablename__ = "comic_tag_association"

    comic_id: Mapped[int] = mapped_column(
        ForeignKey("comics.comic_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagModel(BaseModel):
    __tablename__ = "tags"

    tag_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    is_visible: Mapped[bool] = mapped_column(default=True)
    from_explainxkcd: Mapped[bool] = mapped_column(default=False)

    comics: Mapped[list["ComicModel"]] = relationship(
        back_populates="tags",
        secondary="comic_tag_association",
    )


class ComicModel(BaseModel, TimestampMixin):
    __tablename__ = "comics"

    comic_id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int | None] = mapped_column(SmallInteger)
    slug: Mapped[str | None]
    publication_date: Mapped[date]
    explain_url: Mapped[str | None]
    click_url: Mapped[str | None]
    is_interactive: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="comics",
        secondary="comic_tag_association",
        cascade="all, delete",
        order_by="TagModel.name.asc()",
    )

    translations: Mapped[list["TranslationModel"]] = relationship(
        back_populates="comic",
        cascade="all, delete",
        order_by="TranslationModel.translation_id",
    )

    __table_args__ = (
        Index(
            "uq_comic_number_if_not_extra",
            "number",
            unique=True,
            postgresql_where=(number.isnot(None)),
        ),
        Index(
            "uq_comic_title_if_extra",
            "slug",
            unique=True,
            postgresql_where=(number.is_(None)),
        ),
    )
