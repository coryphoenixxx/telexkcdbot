import asyncio
import logging

import uvloop

from scraper.scrapers.xkcd_origin import XKCDScraper
from shared.api_rest_client import APIRESTClient
from shared.http_client import HttpClient
from shared.utils import ranges, timeit


@timeit
async def main(from_: int = 1, to_: int | None = None, chunk_size: int = 100):
    async with HttpClient() as client:
        scraper = XKCDScraper(client=client)
        api_client = APIRESTClient(client=client)

        if not to_:
            to_ = await scraper.fetch_latest_number()

        for start, end in ranges(start=from_, end=to_, size=chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(number))
                        for number in range(start, end + 1)
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    logging.error(e)
                    raise e
            else:
                comics_data = [task.result() for task in tasks]
                try:
                    async with asyncio.TaskGroup() as tg:
                        tasks = [
                            tg.create_task(api_client.create_comic_with_image(data))
                            for data in comics_data
                        ]
                except* Exception as errors:
                    for e in errors.exceptions:
                        logging.error(e)
                        raise e


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
