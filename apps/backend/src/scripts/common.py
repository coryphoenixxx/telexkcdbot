import asyncclick as click
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
)


def positive_number_callback(ctx, param, value: int) -> int | None:
    if not value:
        return None
    if isinstance(value, int | float) and value > 0:
        return value
    raise click.BadParameter("parameter must be positive")
