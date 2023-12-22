from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import PkIdMixin

if TYPE_CHECKING:
    from src.app.comics.models import ComicModel


class TranslationModel(PkIdMixin, Base):
    __tablename__ = "translations"

    issue_number: Mapped[int] = mapped_column(
        ForeignKey("comics.issue_number", ondelete="CASCADE"),
        primary_key=True,
    )

    title: Mapped[str]
    tooltip: Mapped[str | None]
    transcript: Mapped[str | None]
    news_block: Mapped[str | None]
    images: Mapped[str] = mapped_column(JSON)
    language: Mapped[str] = mapped_column(String(2))
    is_draft: Mapped[bool] = mapped_column(default=False)

    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    def __str__(self):
        return (
            f"{self.__class__.__name__}" f"(issue_number={self.issue_number}, title={self.title})"
        )

    def __repr__(self):
        return str(self)
