import asyncio
import logging
from collections.abc import Callable

from shared.utils import chunked

from scraper.pbar import ProgressBar
from scraper.types import LimitParams

logger = logging.getLogger(__name__)


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
                raise e
        else:
            for task in tasks:
                result = task.result()
                if result:
                    results.append(result)

        await asyncio.sleep(limits.delay)

    if pbar:
        pbar.finish()

    return results
