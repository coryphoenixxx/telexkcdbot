from datetime import date

from sqlalchemy import ForeignKey, Index, SmallInteger, and_, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.infrastructure.database.models import Base, TranslationModel
from api.infrastructure.database.models.mixins import TimestampMixin


class ComicTagAssociation(Base):
    __tablename__ = "comic_tag_association"

    comic_id: Mapped[int] = mapped_column(
        ForeignKey("comics.comic_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagModel(Base):
    __tablename__ = "tags"

    tag_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True)

    comics: Mapped[list["ComicModel"]] = relationship(
        back_populates="tags",
        secondary="comic_tag_association",
    )

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.tag_id}, name={self.name})"

    def __repr__(self):
        return str(self)


class ComicModel(Base, TimestampMixin):
    __tablename__ = "comics"

    comic_id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int | None] = mapped_column(SmallInteger)
    slug: Mapped[str]
    publication_date: Mapped[date]
    explain_url: Mapped[str | None]
    click_url: Mapped[str | None]
    is_interactive: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["TagModel"]] = relationship(
        lazy="selectin",
        back_populates="comics",
        secondary="comic_tag_association",
        cascade="all, delete",
    )

    base_translation: Mapped[TranslationModel] = relationship(
        lazy="selectin",
        back_populates="comic",
        primaryjoin=lambda: and_(
            ComicModel.comic_id == TranslationModel.comic_id,
            TranslationModel.is_draft == false(),
            TranslationModel.language == "EN",
        ),
    )

    translations: Mapped[list["TranslationModel"]] = relationship(
        lazy="selectin",
        back_populates="comic",
        cascade="all, delete",
        primaryjoin=lambda: and_(
            ComicModel.comic_id == TranslationModel.comic_id,
            TranslationModel.is_draft == false(),
            TranslationModel.language != "EN",
        ),
        overlaps="base_translation",
    )

    translation_drafts: Mapped[list["TranslationModel"]] = relationship(
        lazy="selectin",
        back_populates="comic",
        cascade="all, delete",
        primaryjoin=lambda: and_(
            ComicModel.comic_id == TranslationModel.comic_id,
            TranslationModel.is_draft == true(),
            TranslationModel.language != "EN",
        ),
        overlaps="base_translation,translations",
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.comic_id}, number={self.number}, slug={self.slug})"
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
