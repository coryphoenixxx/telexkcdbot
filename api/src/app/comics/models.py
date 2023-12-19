import datetime as dt

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base, PkIdMixin


class ComicTagAssociation(Base, PkIdMixin):
    __tablename__ = "comic_tag_association"
    __table_args__ = (UniqueConstraint("comic_id", "tag_id"),)

    comic_id: Mapped[int] = mapped_column(
        ForeignKey("comics.issue_number", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagModel(Base, PkIdMixin):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(unique=True)

    comics: Mapped[list["ComicModel"]] = relationship(
        back_populates="tags",
        secondary="comic_tag_association",
    )

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self):
        return str(self)


class ComicModel(Base):
    __tablename__ = "comics"

    issue_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    publication_date: Mapped[dt.date]
    xkcd_url: Mapped[str | None]
    reddit_url: Mapped[str | None]
    explain_url: Mapped[str | None]
    link_on_click: Mapped[str | None]
    is_interactive: Mapped[bool] = mapped_column(default=False)
    is_extra: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="comics",
        secondary="comic_tag_association",
        cascade="all, delete",
    )

    def __str__(self):
        return f"{self.__class__.__name__}(issue_number={self.issue_number})"

    def __repr__(self):
        return str(self)
