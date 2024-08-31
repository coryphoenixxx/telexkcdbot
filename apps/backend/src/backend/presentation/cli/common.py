import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

import click
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

base_progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
)


def positive_number_callback(_: click.Context, __: click.core.Option, value: int) -> int | None:
    if not value:
        return None
    if isinstance(value, int | float) and value > 0:
        return value
    raise click.BadParameter("parameter must be positive")


def async_command(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class DatabaseIsEmptyError(Exception): ...


class DatabaseIsNotEmptyError(Exception): ...
