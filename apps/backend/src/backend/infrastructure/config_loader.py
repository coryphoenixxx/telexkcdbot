import functools
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import tomllib
from adaptix import Retort

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class LoadConfigError(Exception):
    message: str


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
        path = os.getenv("CONFIG_PATH")

    try:
        if path is None:
            raise LoadConfigError("Config not provide.")

        if not Path(path).exists():
            raise LoadConfigError(f"Config not found ({path}).")

        toml_data = read_toml(path)
        data = toml_data.get(scope)

        if data is None:
            raise LoadConfigError(f"Invalid scope ({scope}).")

    except LoadConfigError as err:
        sys.exit(err.message)

    return Retort().load(data, typ)
