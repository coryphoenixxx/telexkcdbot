from datetime import date

from sqlalchemy import ForeignKey, Index, SmallInteger, and_, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.infrastructure.database.models import Base, TranslationModel
from api.infrastructure.database.models.mixins import PkIdMixin, TimestampMixin


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


class ComicModel(PkIdMixin, Base, TimestampMixin):
    __tablename__ = "comics"

    number: Mapped[int | None] = mapped_column(SmallInteger)
    slug: Mapped[str]
    publication_date: Mapped[date]
    xkcd_url: Mapped[str | None]
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
        lazy="joined",
        back_populates="comic",
        cascade="all, delete",
        primaryjoin=lambda: and_(
            ComicModel.id == TranslationModel.comic_id,
            TranslationModel.is_draft == false(),
        ),
    )

    drafts: Mapped[list["TranslationModel"]] = relationship(
        back_populates="comic",
        cascade="all, delete",
        primaryjoin=lambda: and_(
            ComicModel.id == TranslationModel.comic_id,
            TranslationModel.is_draft == true(),
        ),
        overlaps="translations",
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}" f"(id={self.id}, number={self.number}, slug={self.slug})"
        )

    def __repr__(self):
        return str(self)

    __table_args__ = (
        Index(
            "uq_number_if_not_extra",
            "number",
            unique=True,
            postgresql_where=(number.isnot(None)),
        ),
        Index(
            "uq_title_if_extra",
            "slug",
            unique=True,
            postgresql_where=(number.is_(None)),
        ),
    )
