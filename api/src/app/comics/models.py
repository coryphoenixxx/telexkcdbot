from datetime import date

from sqlalchemy import ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base
from src.core.database.mixins import CreatedAtMixin, PkIdMixin

from .translations.models import TranslationModel


class ComicTagAssociation(Base):
    __tablename__ = "comic_tag_association"

    comic_id: Mapped[int] = mapped_column(
        ForeignKey("comics.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagModel(PkIdMixin, Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(unique=True)

    comics: Mapped[list["ComicModel"]] = relationship(
        back_populates="tags",
        secondary="comic_tag_association",
    )

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

    def __repr__(self):
        return str(self)


class ComicModel(PkIdMixin, Base, CreatedAtMixin):
    __tablename__ = "comics"

    issue_number: Mapped[int | None] = mapped_column(SmallInteger)
    publication_date: Mapped[date]
    xkcd_url: Mapped[str | None]
    reddit_url: Mapped[str | None]
    explain_url: Mapped[str | None]
    link_on_click: Mapped[str | None]
    is_interactive: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="comics",
        secondary="comic_tag_association",
        cascade="all, delete",
        lazy="selectin",
    )

    translations: Mapped[list["TranslationModel"]] = relationship(
        back_populates="comic",
        cascade="all, delete",
        lazy="joined",
        primaryjoin="and_(ComicModel.id==TranslationModel.comic_id, TranslationModel.is_draft==false())",
    )

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, issue_number={self.issue_number})"

    def __repr__(self):
        return str(self)

    __table_args__ = (
        Index(
            "ix_unique_issue_number_if_not_none",
            "issue_number",
            unique=True,
            postgresql_where=(issue_number.isnot(None)),
        ),
    )
