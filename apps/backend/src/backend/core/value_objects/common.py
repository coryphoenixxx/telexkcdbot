from dataclasses import dataclass
from typing import ClassVar

from backend.core.value_objects.base import ValueObject


@dataclass(slots=True, frozen=True)
class PositiveInt(ValueObject):
    value: int

    def _validate(self) -> None:
        if self.value <= 0:
            raise ValueError("Must be positive integer.")


class ComicID(PositiveInt): ...


class IssueNumber(PositiveInt): ...


class TagID(PositiveInt): ...


class TranslationID(PositiveInt): ...


class TranslationImageID(PositiveInt): ...


@dataclass(slots=True, frozen=True)
class TagName(ValueObject):
    value: str
    _min: ClassVar[int] = 2
    _max: ClassVar[int] = 50

    def _validate(self) -> None:
        if not (self._min <= len(self.value) <= self._max):
            raise ValueError(
                f"Tag name length must be between {self._min} and {self._max} characters."
            )
