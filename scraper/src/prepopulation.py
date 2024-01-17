import asyncio

import uvloop
from src.dtos import XkcdOriginDTO
from src.scrapers.xkcd_origin import XkcdOriginScraper


async def queue_reader(q: asyncio.Queue):
    while True:
        comic: XkcdOriginDTO = await q.get()
        if comic == -1:
            break


async def main():
    q = asyncio.Queue()
    result_task = asyncio.create_task(queue_reader(q))
    await XkcdOriginScraper(q=q).fetch_many(1000, 1100)
    await q.put(-1)
    await result_task


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
