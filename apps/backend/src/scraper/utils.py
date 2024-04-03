import asyncio
from collections.abc import Callable

from shared.utils import chunked

from scraper.pbar import ProgressBar


async def progress_watcher(tasks: list[asyncio.Task], pbar: ProgressBar | None) -> None:
    for t in asyncio.as_completed(tasks):
        if await t:
            pbar.advance()


async def run_concurrently(
    data: list,
    coro: Callable,
    chunk_size: int,
    delay: int,
    pbar: ProgressBar | None,
    **kwargs,
) -> list:
    results = []

    for chunk in chunked(
        lst=data,
        n=chunk_size,
    ):
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(coro(value, **kwargs)) for value in chunk]

                if pbar:
                    tg.create_task(progress_watcher(tasks, pbar))
        except* Exception as errors:
            for e in errors.exceptions:
                raise e
        else:
            for task in tasks:
                if result := task.result():
                    results.append(result)

        await asyncio.sleep(delay)

    if pbar:
        pbar.finish()

    return results
