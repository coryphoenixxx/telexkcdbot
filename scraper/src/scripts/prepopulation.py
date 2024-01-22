import asyncio
import logging

import uvloop
from src.dtos import AggregatedComicDataDTO
from src.http_client import HttpClient
from src.scrapers.explain_xkcd import ExplainXkcdScraper
from src.scrapers.xkcd_origin import XkcdOriginScraper
from src.uploader import APIUploader
from src.utils import async_timed, ranges


async def get_all(
    number: int,
    queue: asyncio.Queue,
    xkcd_scraper: XkcdOriginScraper,
    explain_scraper: ExplainXkcdScraper,
):
    await queue.put(
        AggregatedComicDataDTO(
            origin=await xkcd_scraper.fetch_one(number),
            explain=await explain_scraper.fetch_one(number),
        ),
    )


@async_timed()
async def main(from_: int = 1, to_: int | None = None, chunk_size: int = 100):
    queue = asyncio.Queue()

    async with HttpClient() as client, APIUploader(client, queue):
        xkcd_scraper = XkcdOriginScraper(client)
        explain_scraper = ExplainXkcdScraper(client)

        if not to_:
            to_ = await xkcd_scraper.fetch_latest_number()

        for start, end in ranges(start=from_, end=to_, size=chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    [
                        tg.create_task(
                            get_all(
                                number,
                                queue,
                                xkcd_scraper,
                                explain_scraper,
                            ),
                        )
                        for number in range(start, end + 1)
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    logging.error(e)
                    raise e
            print(f"{start}-{end} SCRAPING FINISHED!")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
