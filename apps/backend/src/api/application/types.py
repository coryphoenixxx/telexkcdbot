import functools
from dataclasses import dataclass
from enum import EnumType, StrEnum
from typing import Annotated, NewType

from annotated_types import Ge, Gt
from shared.config_loader import load_config

TranslationImageID = NewType("TranslationImageID", Annotated[int, Gt(0)])
ComicID = NewType("ComicID", Annotated[int, Gt(0)])
IssueNumber = NewType("IssueNumber", Annotated[int, Gt(0)])
TranslationID = NewType("TranslationID", Annotated[int, Gt(0)])
TranslationDraftID = NewType("TranslationDraftID", Annotated[int, Gt(0)])

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])


class LanguageEnum(StrEnum):
    def __new__(cls, code: str, flag: str):
        member = str.__new__(cls, code)
        member._value_ = code
        member._flag = flag

        return member

    @property
    def flag(self) -> str:
        return self._flag

    @classmethod
    @property
    @functools.cache
    def NON_ENGLISH(cls) -> EnumType:
        return cls.__base__(
            cls.__name__,
            {m.name: (m.value, m.flag) for m in cls if m.name != "EN"}.items(),
        )


@dataclass
class Config:
    allowed_languages: dict[str, str]


def _load_allowed(allowed: dict[str, str] | None = None) -> EnumType:
    lang_code_flag_map: dict[str, str] = {"EN": "🇺🇸"}

    if not allowed:
        allowed = load_config(Config, "other").allowed_languages

    lang_code_flag_map.update(**allowed)

    return LanguageEnum("LanguageCode", {k: (k, v) for k, v in lang_code_flag_map.items()})


LanguageCode = _load_allowed()
