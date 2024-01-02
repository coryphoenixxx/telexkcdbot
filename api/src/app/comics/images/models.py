from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import PkIdMixin
from src.core.types import Dimensions

from .types import ImageVersion

if TYPE_CHECKING:
    from src.app.comics.translations.models import TranslationModel


class TranslationImageModel(PkIdMixin, Base):
    __tablename__ = "translation_images"

    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.id", ondelete="SET NULL"),
    )

    version: Mapped[ImageVersion] = mapped_column(String(20))
    path: Mapped[str]
    converted_path: Mapped[str | None]
    dimensions: Mapped[Dimensions] = composite(mapped_column("width"), mapped_column("height"))

    translation: Mapped["TranslationModel"] = relationship(back_populates="images")
