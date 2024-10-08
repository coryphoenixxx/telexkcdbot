import importlib.resources
import json
from enum import StrEnum
from typing import TypeAlias


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


def _load_language_data() -> dict[str, tuple[str, str, str]]:
    try:
        with (
            importlib.resources.files("assets")
            .joinpath("language_data.json")
            .open("r", encoding="utf-8") as f
        ):
            return {
                code.upper(): (code.upper(), name, native)
                for code, name, native in sorted(json.load(f))
            }
    except (FileNotFoundError, json.JSONDecodeError) as err:
        raise RuntimeError("Failed to load language data.") from err


Language: TypeAlias = LanguageEnum("Language", _load_language_data())  # type: ignore[valid-type, call-arg, arg-type]
