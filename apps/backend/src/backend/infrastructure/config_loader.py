import functools
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import tomllib
from adaptix import Retort

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class LoadConfigError(Exception):
    message: str


@functools.cache
def read_toml(path: str) -> dict[str, Any]:
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def get_config_data(
    typ: type[T],
    scope: str | None = None,
    path: str | None = None,
) -> T:
    if path is None:
        raise LoadConfigError("Config not provide.")

    if not Path(path).exists():
        raise LoadConfigError(f"Config not found ({path}).")

    config_data = read_toml(path)

    if scope:
        scoped_data = config_data.get(scope)
        if scoped_data is None:
            raise LoadConfigError(f"Invalid config scope ({scope}).")
        config_data = scoped_data

    return Retort().load(config_data, typ)


def load_config(
    typ: type[T],
    scope: str | None = None,
    path: str | None = None,
) -> T:
    if path is None:
        path = os.getenv("CONFIG_PATH")
    try:
        return get_config_data(typ, scope, path)
    except LoadConfigError as err:
        sys.exit(err.message)
