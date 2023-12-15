import asyncio
import functools
import time

import aiohttp
from scrapers.xkcd_origin import XkcdOriginScraper


def timeit(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            time.perf_counter() - start_time
            # print(f"Function `{func.__name__}` took {total_time:.4f} seconds")

    return wrapper


@timeit
async def main():
    max_id = 2865
    scraper = XkcdOriginScraper(throttler=asyncio.Semaphore(32))
    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(
                scraper.fetch_json(session, comic_id), name=f"TASK: {comic_id}",
            )
            for comic_id in range(1, max_id + 1)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
