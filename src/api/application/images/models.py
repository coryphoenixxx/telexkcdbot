from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database.base import Base
from api.core.database.mixins import PkIdMixin, TimestampMixin

if TYPE_CHECKING:
    from api.application.translations.models import TranslationModel


class TranslationImageModel(Base, PkIdMixin, TimestampMixin):
    __tablename__ = "translation_images"

    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.id", ondelete="SET NULL"),
    )

    original_rel_path: Mapped[str]
    converted_rel_path: Mapped[str | None]
    thumbnail_rel_path: Mapped[str | None]

    translation: Mapped["TranslationModel"] = relationship(back_populates="images")

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, original_rel_path={self.original_rel_path})"
        )

    def __repr__(self):
        return str(self)
