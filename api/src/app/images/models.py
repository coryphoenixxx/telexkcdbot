from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import CreatedAtMixin, PkIdMixin

from .dtos import TranslationImageResponseDTO
from .types import TranslationImageVersion

if TYPE_CHECKING:
    from src.app.translations.models import TranslationModel


class TranslationImageModel(Base, PkIdMixin, CreatedAtMixin):
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

    def to_dto(self) -> TranslationImageResponseDTO:
        return TranslationImageResponseDTO(
            id=self.id,
            version=self.version,
            path=self.path,
            converted_path=self.converted_path,
        )
