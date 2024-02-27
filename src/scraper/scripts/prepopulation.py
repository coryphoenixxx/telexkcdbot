import asyncio
import logging.config

import uvloop
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from scraper.dtos import XkcdOriginWithExplainScrapedData, XkcdTranslationScrapedData
from scraper.pbar import ProgressBar
from scraper.scrapers import (
    XkcdCNScraper,
    XkcdDEScraper,
    XkcdESScraper,
    XkcdExplainScraper,
    XkcdFRScraper,
    XkcdOriginScraper,
    XkcdOriginWithExplainDataScraper,
    XkcdRUScraper,
)
from scraper.types import LimitParams
from scraper.utils import run_concurrently
from shared.api_rest_client import APIRESTClient
from shared.http_client import AsyncHttpClient
from shared.utils import flatten

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{asctime}::{levelname}::{name}:{lineno} :: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["default"],
            "level": "INFO",
        },
    },
}

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


async def upload_origin_with_explanation(
    api_client: APIRESTClient,
    origin_data: list[XkcdOriginWithExplainScrapedData],
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
    translation_data: list[XkcdTranslationScrapedData],
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


async def main(
    start: int = 1,
    end: int | None = None,
    chunk_size: int = 100,
    delay: int = 0,
):
    async with AsyncHttpClient() as http_client:
        origin_with_explain_scraper = XkcdOriginWithExplainDataScraper(
            origin_scraper=XkcdOriginScraper(client=http_client),
            explain_scraper=XkcdExplainScraper(client=http_client),
        )

        ru_scraper = XkcdRUScraper(client=http_client)
        de_scraper = XkcdDEScraper(client=http_client)
        es_scraper = XkcdESScraper(client=http_client)
        ch_scraper = XkcdCNScraper(client=http_client)
        fr_scraper = XkcdFRScraper(client=http_client)

        api_client = APIRESTClient(http_client)

        if not await api_client.healthcheck():
            return

        if not end:
            end = await origin_with_explain_scraper.origin_scraper.fetch_latest_number()

        limits = LimitParams(start, end, chunk_size, delay)

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
        ) as progress:
            origin_with_explanation = await origin_with_explain_scraper.fetch_many(
                limits,
                progress,
            )

            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(ru_scraper.fetch_many(limits, progress)),
                    tg.create_task(de_scraper.fetch_many(limits, progress)),
                    tg.create_task(es_scraper.fetch_many(limits, progress)),
                    tg.create_task(ch_scraper.fetch_many(limits, progress)),
                    tg.create_task(fr_scraper.fetch_many(limits, progress)),
                ]

            translations = flatten([task.result() for task in tasks])

            number_comic_id_map = await upload_origin_with_explanation(
                api_client, origin_with_explanation, limits, progress,
            )

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
