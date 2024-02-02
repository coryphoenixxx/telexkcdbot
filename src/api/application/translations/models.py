from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.application.images.models import TranslationImageModel
from api.core.database.base import Base
from api.core.database.mixins import PkIdMixin, TimestampMixin
from api.core.types import Language

if TYPE_CHECKING:
    from api.application.comics.models import ComicModel


class TranslationModel(PkIdMixin, Base, TimestampMixin):
    __tablename__ = "translations"

    comic_id: Mapped[int | None] = mapped_column(
        ForeignKey("comics.id", ondelete="CASCADE"),
    )

    title: Mapped[str]
    language: Mapped[Language] = mapped_column(String(2))
    tooltip: Mapped[str | None]
    transcript: Mapped[str | None]
    is_draft: Mapped[bool] = mapped_column(default=False)

    images: Mapped[list["TranslationImageModel"]] = relationship(
        back_populates="translation",
        lazy="joined",
    )
    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, comic_id={self.comic_id}, "
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
    )
