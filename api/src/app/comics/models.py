from datetime import date

from sqlalchemy import ForeignKey, Index, SmallInteger, and_, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.translations.models import TranslationModel
from src.core.database.base import Base
from src.core.database.mixins import PkIdMixin, TimestampMixin

from .dtos.response import ComicResponseDTO, ComicResponseWithTranslationsDTO


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

    issue_number: Mapped[int | None] = mapped_column(SmallInteger)
    slug: Mapped[str]
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
            f"{self.__class__.__name__}"
            f"(id={self.id}, issue_number={self.issue_number}, slug={self.slug})"
        )

    def __repr__(self):
        return str(self)

    __table_args__ = (
        Index(
            "uq_issue_number_if_not_extra",
            "issue_number",
            unique=True,
            postgresql_where=(issue_number.isnot(None)),
        ),
        Index(
            "uq_title_if_extra",
            "slug",
            unique=True,
            postgresql_where=(issue_number.is_(None)),
        ),
    )

    def to_dto(
        self,
        with_translations: bool = True,
    ) -> ComicResponseDTO | ComicResponseWithTranslationsDTO:
        if with_translations:
            return ComicResponseWithTranslationsDTO(
                id=self.id,
                issue_number=self.issue_number,
                publication_date=self.publication_date,
                xkcd_url=self.xkcd_url,
                explain_url=self.explain_url,
                reddit_url=self.reddit_url,
                link_on_click=self.link_on_click,
                is_interactive=self.is_interactive,
                tags=sorted([tag.name for tag in self.tags]),
                translations=[t.to_dto() for t in self.translations],
            )
        else:
            return ComicResponseDTO(
                id=self.id,
                issue_number=self.issue_number,
                publication_date=self.publication_date,
                xkcd_url=self.xkcd_url,
                explain_url=self.explain_url,
                reddit_url=self.reddit_url,
                link_on_click=self.link_on_click,
                is_interactive=self.is_interactive,
                tags=[tag.name for tag in self.tags],
            )
