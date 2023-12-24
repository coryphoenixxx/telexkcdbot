from typing import Any


def cast_or_none(type_: type[Any], value: Any) -> type[Any] | None:
    if value:
        return type_(value)
