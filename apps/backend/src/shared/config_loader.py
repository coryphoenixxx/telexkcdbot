import functools
import os
import tomllib
from pathlib import Path
from typing import TypeVar

from adaptix import Retort

T = TypeVar("T")
DEFAULT_CONFIG_PATH = "./config/config.toml"


@functools.cache
def read_toml(path: str) -> dict:
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def load_config(
    typ: type[T],
    scope: str | None = None,
    path: str | None = None,
) -> T:
    if path is None:
        path = os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH)

    data = read_toml(path)

    if scope is not None:
        data = data[scope]

    dcf = Retort()

    return dcf.load(data, typ)
