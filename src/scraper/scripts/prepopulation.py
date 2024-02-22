import asyncio
import logging

import uvloop
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from scraper.dtos import XkcdOriginData, XkcdTranslation
from scraper.scrapers import XkcdOriginScraper
from scraper.scrapers.translation_scrapers.CN import XkcdCNScraper
from scraper.scrapers.translation_scrapers.DE import XkcdDEScraper
from scraper.scrapers.translation_scrapers.ES import XkcdESScraper
from scraper.scrapers.translation_scrapers.FR import XkcdFRScraper
from scraper.scrapers.translation_scrapers.RU import XkcdRUScraper
from scraper.types import LimitParams
from scraper.utils import ProgressBar, run_concurrently
from shared.api_rest_client import APIRESTClient
from shared.http_client import AsyncHttpClient
from shared.utils import flatten

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def upload_origin(
    api_client: APIRESTClient,
    origin_data: list[XkcdOriginData],
    limits: LimitParams,
    progress: Progress,
) -> dict[int, int]:
    number_comic_id_map = {}

    results = await run_concurrently(
        data=origin_data,
        coro=api_client.create_comic_with_image,
        limits=limits,
        pbar=ProgressBar(progress, "Origin uploading...", len(origin_data)),
    )

    for r in results:
        number_comic_id_map |= r

    return number_comic_id_map


async def upload_translations(
    api_client: APIRESTClient,
    number_comic_id_map: dict[int, int],
    translation_data: list[XkcdTranslation],
    limits: LimitParams,
    progress: Progress,
):
    await run_concurrently(
        data=translation_data,
        coro=api_client.add_translation_with_image,
        limits=limits,
        number_comic_id_map=number_comic_id_map,
        pbar=ProgressBar(progress, "Translations uploading...", len(translation_data)),
    )


async def main(start: int = 1, end: int | None = None, chunk_size: int = 100, delay: int = 0):
    async with AsyncHttpClient() as http_client:
        xkcd_origin_scraper = XkcdOriginScraper(client=http_client)

        xkcd_ru_scraper = XkcdRUScraper(client=http_client)
        xkcd_de_scraper = XkcdDEScraper(client=http_client)
        xkcd_es_scraper = XkcdESScraper(client=http_client)
        xkcd_ch_scraper = XkcdCNScraper(client=http_client)
        xkcd_fr_scraper = XkcdFRScraper(client=http_client)

        api_client = APIRESTClient(http_client)

        if not await api_client.healthcheck():
            return

        if not end:
            end = await xkcd_origin_scraper.fetch_latest_number()

        limits = LimitParams(start, end, chunk_size, delay)

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            refresh_per_second=5,
        ) as progress:
            origin_data = await xkcd_origin_scraper.fetch_many(limits, progress)

            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(xkcd_ru_scraper.fetch_many(limits, progress)),
                    tg.create_task(xkcd_de_scraper.fetch_many(limits, progress)),
                    tg.create_task(xkcd_es_scraper.fetch_many(limits, progress)),
                    tg.create_task(xkcd_ch_scraper.fetch_many(limits, progress)),
                    tg.create_task(xkcd_fr_scraper.fetch_many(limits, progress)),
                ]

            translations = flatten([task.result() for task in tasks])

            number_comic_id_map = await upload_origin(api_client, origin_data, limits, progress)

            await upload_translations(
                api_client,
                number_comic_id_map,
                translations,
                limits,
                progress,
            )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
