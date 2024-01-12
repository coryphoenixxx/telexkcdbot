from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.images.models import TranslationImageModel
from src.app.translations.dtos.response import TranslationResponseDTO
from src.core.database.base import Base
from src.core.database.mixins import PkIdMixin
from src.core.types import Language

if TYPE_CHECKING:
    from src.app.comics.models import ComicModel


class TranslationModel(PkIdMixin, Base):
    __tablename__ = "translations"

    comic_id: Mapped[int | None] = mapped_column(
        ForeignKey("comics.id", ondelete="CASCADE"),
    )

    title: Mapped[str]
    language: Mapped[Language] = mapped_column(String(2))
    tooltip: Mapped[str | None]
    transcript: Mapped[str | None]
    news_block: Mapped[str | None]
    is_draft: Mapped[bool] = mapped_column(default=False)

    images: Mapped[list["TranslationImageModel"]] = relationship(
        back_populates="translation",
        lazy="joined",
    )
    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"({self.id=}, {self.comic_id=}, {self.language}, {self.title=})"
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

    def to_dto(self) -> TranslationResponseDTO:
        return TranslationResponseDTO(
            id=self.id,
            language=self.language,
            title=self.title,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news_block=self.news_block,
            images=[image.to_dto() for image in self.images],
            is_draft=self.is_draft,
        )
