from typing import TYPE_CHECKING

from shared.types import LanguageCode
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.infrastructure.database.models import Base
from api.infrastructure.database.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from . import ComicModel


class TranslationImageModel(Base, TimestampMixin):
    __tablename__ = "translation_images"

    image_id: Mapped[int] = mapped_column(primary_key=True)
    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.translation_id", ondelete="SET NULL"),
    )
    original_rel_path: Mapped[str]
    converted_rel_path: Mapped[str | None]
    thumbnail_rel_path: Mapped[str | None]

    translation: Mapped["TranslationModel"] = relationship(back_populates="images")

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.image_id}, original_rel_path={self.original_rel_path})"
        )

    def __repr__(self):
        return str(self)


class TranslationModel(Base, TimestampMixin):
    __tablename__ = "translations"

    translation_id: Mapped[int] = mapped_column(primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.comic_id", ondelete="CASCADE"))
    title: Mapped[str]
    language: Mapped[LanguageCode] = mapped_column(String(2))
    tooltip: Mapped[str] = mapped_column(default="")
    transcript_raw: Mapped[str] = mapped_column(default="")
    translator_comment: Mapped[str] = mapped_column(default="")
    source_link: Mapped[str | None]
    is_draft: Mapped[bool] = mapped_column(default=False)
    images: Mapped[list["TranslationImageModel"]] = relationship(
        back_populates="translation",
        lazy="selectin",
    )

    searchable_text: Mapped[str]

    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    original_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "translations.translation_id",
            ondelete="CASCADE",
        ),
    )
    drafts: Mapped[list["TranslationModel"]] = relationship(
        "TranslationModel",
        back_populates="original",
        lazy="joined",
        join_depth=2,
    )
    original: Mapped["TranslationModel"] = relationship(
        "TranslationModel",
        back_populates="drafts",
        remote_side=[translation_id],
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.translation_id}, comic_id={self.comic_id}, "
            f"language={self.language}, title={self.title})"
        )

    def __repr__(self):
        return str(self)

    __table_args__ = (
        Index(
            "uq_translation_if_not_draft",
            "language",
            "comic_id",
            unique=True,
            postgresql_where=(~is_draft),
        ),
        Index(
            "ix_translations_searchable_text",
            "searchable_text",
            postgresql_using="pgroonga",
        ),
    )
