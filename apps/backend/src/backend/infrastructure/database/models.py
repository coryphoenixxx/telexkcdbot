from copy import copy
from datetime import date
from pathlib import Path

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.application.comic.dtos import (
    ComicResponseDTO,
    TagResponseDTO,
    TranslationImageResponseDTO,
    TranslationResponseDTO,
)
from backend.application.utils import cast_or_none
from backend.core.value_objects import (
    ComicID,
    IssueNumber,
    Language,
    TagID,
    TagName,
    TranslationID,
    TranslationImageID,
)


class BaseModel(DeclarativeBase):
    __abstract__ = True


BaseModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class TimestampMixin:
    created_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )


class TranslationImageModel(BaseModel, TimestampMixin):
    __tablename__ = "translation_images"

    image_id: Mapped[int] = mapped_column(primary_key=True)
    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.translation_id", ondelete="SET NULL"),
    )
    original: Mapped[str]
    converted: Mapped[str | None]

    translation: Mapped["TranslationModel"] = relationship(back_populates="image")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.image_id}, original_rel_path={self.original})"

    def __repr__(self) -> str:
        return str(self)

    def to_dto(self) -> TranslationImageResponseDTO:
        return TranslationImageResponseDTO(
            id=TranslationImageID(self.image_id),
            translation_id=TranslationID(self.translation_id) if self.translation_id else None,
            original=Path(self.original),
            converted=cast_or_none(Path, self.converted),
        )


class TranslationModel(BaseModel, TimestampMixin):
    __tablename__ = "translations"

    translation_id: Mapped[int] = mapped_column(primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.comic_id", ondelete="CASCADE"))
    title: Mapped[str]
    language: Mapped[str] = mapped_column(String(2))
    tooltip: Mapped[str] = mapped_column(default="")
    raw_transcript: Mapped[str] = mapped_column(default="")
    translator_comment: Mapped[str] = mapped_column(default="")
    source_url: Mapped[str | None]
    # TODO: change to state (under review, approved, published)
    is_draft: Mapped[bool] = mapped_column(default=False)

    image: Mapped[TranslationImageModel | None] = relationship(
        back_populates="translation",
        single_parent=True,
    )

    searchable_text: Mapped[str] = mapped_column(Text)

    comic: Mapped["ComicModel"] = relationship(back_populates="translations")

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(id={self.translation_id}, comic_id={self.comic_id}, "
            f"language={self.language}, title={self.title})"
        )

    def __repr__(self) -> str:
        return str(self)

    __table_args__ = (
        Index(
            "uq_translation_if_not_draft",
            "language",
            "comic_id",
            unique=True,
            postgresql_where=(~is_draft),
        ),
        Index(
            "ix_translations_searchable_text",
            "searchable_text",
            postgresql_using="pgroonga",
        ),
    )

    def to_dto(self) -> TranslationResponseDTO:
        return TranslationResponseDTO(
            id=TranslationID(self.translation_id),
            comic_id=ComicID(self.comic_id),
            language=Language(self.language),
            title=self.title,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment=self.translator_comment,
            image=self.image.to_dto() if self.image else None,
            source_url=self.source_url,
            is_draft=self.is_draft,
        )


class ComicTagAssociation(BaseModel):
    __tablename__ = "comic_tag_association"

    comic_id: Mapped[int] = mapped_column(
        ForeignKey("comics.comic_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagModel(BaseModel):
    __tablename__ = "tags"

    tag_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    is_blacklisted: Mapped[bool] = mapped_column(default=False)

    comics: Mapped[list["ComicModel"]] = relationship(
        back_populates="tags",
        secondary="comic_tag_association",
    )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.tag_id}, name={self.name})"

    def __repr__(self) -> str:
        return str(self)

    def to_dto(self) -> TagResponseDTO:
        return TagResponseDTO(
            id=TagID(self.tag_id),
            name=TagName(self.name),
            is_blacklisted=self.is_blacklisted,
        )


class ComicModel(BaseModel, TimestampMixin):
    __tablename__ = "comics"

    comic_id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int | None] = mapped_column(SmallInteger)
    slug: Mapped[str | None]
    publication_date: Mapped[date]
    explain_url: Mapped[str | None]
    click_url: Mapped[str | None]
    is_interactive: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="comics",
        secondary="comic_tag_association",
        cascade="all, delete",
        order_by="TagModel.name.asc()",
    )

    translations: Mapped[list["TranslationModel"]] = relationship(
        back_populates="comic",
        cascade="all, delete",
    )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(id={self.comic_id}, number={self.number}, slug={self.slug})"
        )

    def __repr__(self) -> str:
        return str(self)

    __table_args__ = (
        Index(
            "uq_comic_number_if_not_extra",
            "number",
            unique=True,
            postgresql_where=(number.isnot(None)),
        ),
        Index(
            "uq_comic_title_if_extra",
            "slug",
            unique=True,
            postgresql_where=(number.is_(None)),
        ),
    )

    @staticmethod
    def _separate_translations(
        translations: list["TranslationModel"],
    ) -> tuple["TranslationModel", list["TranslationModel"]]:
        for idx, tr in enumerate(translations):
            if tr.language == Language.EN:
                original = translations.pop(idx)
                return original, translations
        raise ValueError("Comic model hasn't english translations.")

    def to_dto(self) -> ComicResponseDTO:
        original, translations = self._separate_translations(copy(self.translations))

        return ComicResponseDTO(
            id=ComicID(self.comic_id),
            number=IssueNumber(self.number) if self.number else None,
            title=original.title,
            translation_id=TranslationID(original.translation_id),
            publication_date=self.publication_date,
            tooltip=original.tooltip,
            xkcd_url=original.source_url,
            explain_url=self.explain_url,
            click_url=self.click_url,
            is_interactive=self.is_interactive,
            tags=[tag.to_dto() for tag in self.tags],
            image=(original.image.to_dto() if original.image else None),
            has_translations=[Language(tr.language) for tr in translations],
            translations=[t.to_dto() for t in translations],
        )
