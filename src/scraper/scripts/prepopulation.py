import asyncio
import logging

import uvloop
from alive_progress import alive_bar

from scraper.scrapers.xkcd_origin import XKCDScraper
from shared.api_rest_client import APIRESTClient
from shared.http_client import HttpClient
from shared.utils import ranges, timeit

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("alive_progress")


@timeit
async def main(from_: int = 1, to_: int | None = None, chunk_size: int = 100):
    async with HttpClient() as client:
        scraper = XKCDScraper(client=client)
        api_client = APIRESTClient(client=client)

        if await api_client.healthcheck():
            logger.info("Starting scraping...")

        if not to_:
            to_ = await scraper.fetch_latest_number()

        comics_data = []
        with alive_bar(total=to_, title="Xkcd origin scraping...:", title_length=25) as bar:
            for start, end in ranges(start=from_, end=to_, size=chunk_size):
                try:
                    async with asyncio.TaskGroup() as tg:
                        tasks = [
                            tg.create_task(scraper.fetch_one(number, bar))
                            for number in range(start, end + 1)
                        ]
                except* Exception as errors:
                    for e in errors.exceptions:
                        logger.error(e)
                        raise e
                else:
                    [comics_data.append(task.result()) for task in tasks]

        logger.info("Successfully scraped.")

        with alive_bar(total=to_, title="Uploading to API...:", title_length=25) as bar:
            for start, end in ranges(start=from_, end=to_, size=chunk_size):
                try:
                    async with asyncio.TaskGroup() as tg:
                        tasks = [
                            tg.create_task(api_client.create_comic_with_image(data, bar))
                            for data in comics_data[start - 1 : end]
                        ]
                except* Exception as errors:
                    for e in errors.exceptions:
                        logger.error(e)
                        raise e

        logger.info("Successfully uploaded.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main(chunk_size=100))
