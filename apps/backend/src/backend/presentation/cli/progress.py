import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from itertools import batched
from typing import Any, TypeVar

from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

T = TypeVar("T")


def progress_factory() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        refresh_per_second=5,
    )


class ProgressBar:
    def __init__(self, progress: Progress, desc: str, total: int | None = None) -> None:
        self._progress = progress
        self._total = total
        self._task_id = self._progress.add_task(description=desc, total=total)
        self._counter = 0

    def advance(self, step: int = 1) -> None:
        self._progress.update(self._task_id, advance=step)
        self._counter += 1

    def finish(self) -> None:
        self._progress.stop_task(self._task_id)

        if not self._total:
            column = self._progress.columns[-2]

            if isinstance(column, MofNCompleteColumn):
                for task in self._progress.tasks:
                    if task.id == self._task_id:
                        task.total = self._counter
                        column.render(task)


@dataclass(slots=True)
class ProgressChunkedRunner:
    progress: Progress
    chunk_size: int
    delay: float

    async def run(
        self,
        desc: str,
        data: list[Any],
        coro: Callable[..., Coroutine[Any, Any, Any]],
        known_total: bool = True,
        **kwargs: Any,
    ) -> list[Any]:
        results = []

        pbar = ProgressBar(self.progress, desc, total=len(data) if known_total else None)

        for chunk in batched(iterable=data, n=self.chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [tg.create_task(coro(value, **kwargs)) for value in chunk]
                    for fut in asyncio.as_completed(tasks):
                        if result := await fut:
                            results.append(result)
                            pbar.advance()
            except* Exception as errors:
                for _ in errors.exceptions:
                    raise
            await asyncio.sleep(self.delay)

        pbar.finish()

        return results
