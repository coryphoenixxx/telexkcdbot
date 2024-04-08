import functools
from dataclasses import dataclass
from enum import EnumType, StrEnum
from typing import Annotated, NewType

from annotated_types import Ge, Gt, Len
from shared.config_loader import load_config

ComicID = NewType("ComicID", Annotated[int, Gt(0)])
IssueNumber = NewType("IssueNumber", Annotated[int, Gt(0)])
TranslationID = NewType("TranslationID", Annotated[int, Gt(0)])
TranslationImageID = NewType("TranslationImageID", Annotated[int, Gt(0)])
TranslationDraftID = NewType("TranslationDraftID", Annotated[int, Gt(0)])

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])

LangCode = NewType("LangCode", Annotated[str, Len(2)])
FlagType = NewType("FlagType", Annotated[str, Len(2)])


class LanguageEnum(StrEnum):
    def __new__(cls, code: LangCode, flag: FlagType):
        member = str.__new__(cls, code)
        member._value_ = code
        member._flag = flag

        return member

    @property
    def flag(self) -> FlagType:
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
    allowed_languages: dict[LangCode, FlagType]


def _load_allowed(allowed: dict[LangCode, FlagType] | None = None) -> EnumType:
    lang_code_flag_map = {"EN": "🇺🇸"}

    if not allowed:
        allowed = load_config(Config, "other").allowed_languages

    lang_code_flag_map.update(**allowed)

    return LanguageEnum("Language", {k: (k, v) for k, v in lang_code_flag_map.items()})


Language = _load_allowed()
