from dataclasses import dataclass

from backend.application.common.exceptions import BaseAppError
from backend.core.value_objects import ComicID, IssueNumber


@dataclass(slots=True)
class ComicNotFoundError(BaseAppError):
    value: ComicID | IssueNumber | str

    @property
    def message(self) -> str:
        match self.value:
            case ComicID():
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
    title: str

    @property
    def message(self) -> str:
        return f"An extra comic with this title (`{self.title}`) already exists."
