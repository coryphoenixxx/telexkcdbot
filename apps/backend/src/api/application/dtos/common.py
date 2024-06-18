import datetime
import importlib.resources
import json
from dataclasses import dataclass
from enum import EnumType, StrEnum
from pathlib import Path
from typing import Annotated, NewType

from annotated_types import Ge, Len, MaxLen, MinLen
from shared.my_types import ImageFormat, Order

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])
Alpha2LangCode = NewType("Alpha2LangCode", Annotated[str, Len(2)])
Tag = NewType("Tag", Annotated[str, MinLen(2), MaxLen(50)])


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
    with importlib.resources.open_text("data", "language_data.json") as f:
        langs = json.load(f)

    return LanguageEnum(
        "Language",
        {code.upper(): (code.upper(), name, native) for code, name, native in langs},
    )


Language = _build_language_type()

Limit = NewType("Limit", Annotated[int, Ge(0)])
Offset = NewType("Offset", Annotated[int, Ge(0)])


class TagParam(StrEnum):
    AND = "AND"
    OR = "OR"


@dataclass(slots=True)
class DateRange:
    start: datetime.date | None
    end: datetime.date | None


@dataclass(slots=True)
class ComicFilterParams:
    q: str | None = None
    limit: Limit | None = None
    offset: Offset | None = None
    date_range: DateRange | None = None
    order: Order | None = None
    tags: list[Tag] | None = None
    tag_param: TagParam | None = None


@dataclass(slots=True)
class TranslationImageMeta:
    number: int | None
    title: str
    language: Alpha2LangCode
    is_draft: bool


@dataclass
class Dimensions:
    width: int
    height: int


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions
