from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database.base import Base
from api.core.database.mixins import PkIdMixin, TimestampMixin

from .dtos import TranslationImageResponseDTO
from .types import TranslationImageVersion

if TYPE_CHECKING:
    from api.application.translations.models import TranslationModel


class TranslationImageModel(Base, PkIdMixin, TimestampMixin):
    __tablename__ = "translation_images"

    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.id", ondelete="SET NULL"),
    )

    version: Mapped[TranslationImageVersion] = mapped_column(String(10))
    path: Mapped[str]
    converted_path: Mapped[str | None]

    translation: Mapped["TranslationModel"] = relationship(back_populates="images")

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, path={self.path})"

    def __repr__(self):
        return str(self)

    __table_args__ = (
        Index(
            "uq_version_per_translation",
            "version", "translation_id",
            unique=True,
            postgresql_where=(translation_id.isnot(None)),
        ),
    )

    def to_dto(self) -> TranslationImageResponseDTO:
        return TranslationImageResponseDTO(
            id=self.id,
            version=self.version,
            path=self.path,
            converted_path=self.converted_path,
        )
