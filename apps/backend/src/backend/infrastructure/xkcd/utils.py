import asyncio
from collections.abc import Callable, Generator, Sequence
from typing import TypeVar

from backend.infrastructure.xkcd.pbar import CustomProgressBar

T = TypeVar("T")


def chunked(seq: Sequence["T"], n: int) -> Generator[list["T"], None, None]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


async def progress_watcher(tasks: list[asyncio.Task], pbar: CustomProgressBar | None) -> None:
    for t in asyncio.as_completed(tasks):
        if await t:
            pbar.advance()


async def run_concurrently(
    data: list,
    coro: Callable,
    chunk_size: int,
    delay: int,
    pbar: CustomProgressBar | None,
    **kwargs,
) -> list:
    results = []

    for chunk in chunked(seq=data, n=chunk_size):
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(coro(value, **kwargs)) for value in chunk]

                if pbar:
                    tg.create_task(progress_watcher(tasks, pbar))
        except* Exception as errors:
            for _ in errors.exceptions:
                raise
        else:
            for task in tasks:
                result = task.result()
                if result:
                    results.append(result)

        await asyncio.sleep(delay)

    if pbar:
        pbar.finish()

    return results
