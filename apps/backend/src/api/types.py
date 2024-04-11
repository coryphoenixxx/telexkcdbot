import importlib.resources
import json
from enum import EnumType, StrEnum
from typing import Annotated, NewType

from annotated_types import Ge, Gt, Len

ComicID = NewType("ComicID", Annotated[int, Gt(0)])
IssueNumber = NewType("IssueNumber", Annotated[int, Gt(0)])
TranslationID = NewType("TranslationID", Annotated[int, Gt(0)])
TranslationImageID = NewType("TranslationImageID", Annotated[int, Gt(0)])

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])

Alpha2LangCode = NewType("Alpha2LangCode", Annotated[str, Len(2)])


class LanguageEnum(StrEnum):
    def __new__(cls, code: Alpha2LangCode, name: str, native: str):
        member = str.__new__(cls, code)
        member._value_ = code
        member._name = name
        member._native = native

        return member

    @property
    def name(self):
        return self._name

    @property
    def native(self):
        return self._native


def _build_language_type() -> EnumType:
    with importlib.resources.open_text("data", "language_data.json") as f:
        langs = json.load(f)

    return LanguageEnum(
        "Language",
        {code.upper(): (code.upper(), name, native) for code, name, native in langs},
    )


Language = _build_language_type()
