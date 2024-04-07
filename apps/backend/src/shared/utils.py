from collections.abc import Generator, Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def cast_or_none(cast_to: type["T"], value: Any) -> type["T"] | None:
    if value:
        return cast_to(value)


def chunked(seq: Sequence["T"], n: int) -> Generator[list["T"], None, None]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def flatten(matrix: list[list["T"]]) -> list["T"]:
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list
