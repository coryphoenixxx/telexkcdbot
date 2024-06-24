from dataclasses import dataclass

from .base import BaseConflictError, BaseNotFoundError


@dataclass
class ComicNotFoundError(BaseNotFoundError):
    message: str = "A comic not found."


@dataclass
class ComicNumberAlreadyExistsError(BaseConflictError):
    message: str = "A comic with this issue number already exists."


@dataclass
class ExtraComicTitleAlreadyExistsError(BaseConflictError):
    message: str = "An extra comic with this title already exists."
