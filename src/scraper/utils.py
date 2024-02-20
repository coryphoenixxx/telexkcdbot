import asyncio
import logging
from collections.abc import Callable

from rich.progress import MofNCompleteColumn, Progress
from shared.utils import chunked

from scraper.types import LimitParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProgressBar:
    def __init__(self, progress: Progress, desc: str, total: int | None = None):
        self._progress = progress
        self._total = total
        self._task_id = self._progress.add_task(description=desc, total=total)
        self._counter = 0

    def update(self, step: int = 1):
        self._progress.update(self._task_id, advance=step)
        self._counter += 1

    def finish(self):
        self._progress.stop_task(self._task_id)

        if not self._total:
            col: MofNCompleteColumn = self._progress.columns[-2]

            for task in self._progress.tasks:
                if task.id == self._task_id:
                    task.total = self._counter
                    col.render(task)


async def run_concurrently(
    data: list,
    coro: Callable,
    limits: LimitParams,
    pbar: ProgressBar | None,
    **kwargs,
) -> list:
    results = []

    for chunk in chunked(
        lst=data,
        n=limits.chunk_size,
    ):
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(coro(value, pbar=pbar, **kwargs)) for value in chunk]
        except* Exception as errors:
            for e in errors.exceptions:
                logger.error(e)
                raise e
        else:
            for task in tasks:
                result = task.result()
                if result:
                    results.append(result)
    if pbar:
        pbar.finish()

    return results
