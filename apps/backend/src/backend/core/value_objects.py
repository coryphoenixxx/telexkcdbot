import importlib.resources
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, NewType, TypeAlias
from uuid import UUID


@dataclass(slots=True)
class ValueObject:
    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None: ...


@dataclass(slots=True)
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


TempFileID = NewType("TempFileID", UUID)


@dataclass(slots=True)
class TagName(ValueObject):
    value: str
    _min: ClassVar[int] = 2
    _max: ClassVar[int] = 50

    def _validate(self) -> None:
        if not (self._min <= len(self.value) <= self._max):
            raise ValueError(
                f"Tag name length must be between {self._min} and {self._max} characters."
            )


class LanguageEnum(StrEnum):
    def __new__(cls, code: str, name: str, native: str) -> str:  # type: ignore[misc]
        member = str.__new__(cls, code)
        member._value_ = code
        member._name = name  # type: ignore[attr-defined] # noqa: SLF001
        member._native = native  # type: ignore[attr-defined] # noqa: SLF001

        return member

    @property
    def name(self) -> str:
        return self._name  # type: ignore[attr-defined, no-any-return]

    @property
    def native(self) -> str:
        return self._native  # type: ignore[attr-defined, no-any-return]


def _get_language_data() -> dict[str, tuple[str, str, str]]:
    with (
        importlib.resources.files("assets")
        .joinpath("language_data.json")
        .open("r", encoding="utf-8") as f
    ):
        return {
            code.upper(): (code.upper(), name, native)
            for code, name, native in sorted(json.load(f))
        }


Language: TypeAlias = LanguageEnum("Language", _get_language_data())  # type: ignore[valid-type, call-arg, arg-type]
