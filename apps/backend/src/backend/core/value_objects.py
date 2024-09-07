import importlib.resources
import json
from enum import EnumType, StrEnum
from typing import Annotated, NewType
from uuid import UUID

from annotated_types import Len


class PositiveInt(int):
    def __new__(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Must be positive.")
        return super().__new__(cls, value)


class ComicID(PositiveInt): ...


class IssueNumber(PositiveInt): ...


class TagID(PositiveInt): ...


class TranslationID(PositiveInt): ...


class TranslationImageID(PositiveInt): ...


TempFileID = NewType("TempFileID", UUID)


class TagName(str):
    __slots__ = ()

    MIN_LENGTH = 2
    MAX_LENGTH = 50

    def __new__(cls, value: str) -> "TagName":
        length = len(value)
        if not (cls.MIN_LENGTH <= length <= cls.MAX_LENGTH):
            raise ValueError(
                f"Tag name length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} "
                f"characters. (Given: `{value}`)"
            )
        return super().__new__(cls, value)


Alpha2LangCode = NewType("Alpha2LangCode", Annotated[str, Len(2)])


class LanguageEnum(StrEnum):
    def __new__(cls, code: Alpha2LangCode, name: str, native: str) -> str:
        member = str.__new__(cls, code)
        member._value_ = code
        member._name = name  # noqa: SLF001
        member._native = native  # noqa: SLF001

        return member

    @property
    def name(self) -> str:
        return self._name

    @property
    def native(self) -> str:
        return self._native


def _build_language_type() -> EnumType:
    with (
        importlib.resources.files("assets")
        .joinpath("language_data.json")
        .open("r", encoding="utf-8") as f
    ):
        langs = json.load(f)

    return LanguageEnum(
        "Language",
        {code.upper(): (code.upper(), name, native) for code, name, native in langs},
    )


Language = _build_language_type()
