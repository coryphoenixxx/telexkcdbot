from dataclasses import dataclass

from backend.domain.exceptions import BaseAppError
from backend.domain.value_objects import (
    ComicId,
    IssueNumber,
    Language,
    PositiveInt,
    TranslationTitle,
)


@dataclass(slots=True)
class ComicNotFoundError(BaseAppError):
    value: ComicId | IssueNumber | str

    @property
    def message(self) -> str:
        match self.value:
            case ComicId():
                return f"A comic (id={self.value.value}) not found."
            case IssueNumber():
                return f"A comic (number={self.value.value}) not found."
            case str():
                return f"A comic (slug=`{self.value}`) not found."
            case _:
                raise ValueError("Invalid type.")


@dataclass(slots=True)
class ComicNumberAlreadyExistsError(BaseAppError):
    number: IssueNumber

    @property
    def message(self) -> str:
        return f"A comic with this issue number ({self.number.value}) already exists."


@dataclass(slots=True)
class ExtraComicTitleAlreadyExistsError(BaseAppError):
    title: TranslationTitle

    @property
    def message(self) -> str:
        return f"An extra comic with this title (`{self.title.value}`) already exists."


@dataclass(slots=True)
class TagNotFoundError(BaseAppError):
    tag_id: int

    @property
    def message(self) -> str:
        return f"A tag (id={self.tag_id}) not found."


@dataclass(slots=True)
class TagNameAlreadyExistsError(BaseAppError):
    name: str

    @property
    def message(self) -> str:
        return f"A tag (name=`{self.name}`) already exists."


@dataclass(slots=True)
class TranslationAlreadyExistsError(BaseAppError):
    language: Language

    @property
    def message(self) -> str:
        return f"A comic already has a translation into this language ({self.language})."


@dataclass(slots=True)
class TranslationNotFoundError(BaseAppError):
    value: PositiveInt | Language

    @property
    def message(self) -> str:
        match self.value:
            case PositiveInt():
                return f"Translation (id={self.value.value}) not found."
            case Language():
                return f"Translation (lang=`{self.value}`) not found."
            case _:
                raise ValueError("Invalid type.")
