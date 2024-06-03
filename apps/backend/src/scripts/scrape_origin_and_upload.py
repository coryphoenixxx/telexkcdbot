import asyncio

import asyncclick as click
import uvloop
from rich.progress import Progress
from scraper.dtos import XkcdOriginWithExplainScrapedData
from scraper.my_types import LimitParams
from scraper.pbar import ProgressBar
from scraper.scrapers import (
    XkcdExplainScraper,
    XkcdOriginScraper,
    XkcdOriginWithExplainDataScraper,
)
from scraper.utils import run_concurrently
from scripts.common import positive_number_callback
from scripts.common import progress as base_progress
from shared.api_rest_client import APIRESTClient
from shared.http_client import AsyncHttpClient


async def upload_origin_with_explanation(
    api_client: APIRESTClient,
    origin_data: list[XkcdOriginWithExplainScrapedData],
    limits: LimitParams,
    progress: Progress,
):
    await run_concurrently(
        data=origin_data,
        coro=api_client.create_comic_with_image,
        chunk_size=limits.chunk_size,
        delay=limits.delay,
        pbar=ProgressBar(progress, "Origin data uploading...", len(origin_data)),
    )


@click.command()
@click.option("--start", type=int, default=1, callback=positive_number_callback)
@click.option("--end", type=int, callback=positive_number_callback)
@click.option("--chunk_size", type=int, default=100, callback=positive_number_callback)
@click.option("--delay", type=float, default=0.01, callback=positive_number_callback)
@click.option("--api-url", type=str, default="http://127.0.0.1:8000/api")
async def main(start: int, end: int | None, chunk_size: int, delay: int, api_url: str):
    async with AsyncHttpClient() as http_client:
        api_client = APIRESTClient(api_url, http_client)

        await api_client.healthcheck()

        origin_with_explain_scraper = XkcdOriginWithExplainDataScraper(
            origin_scraper=XkcdOriginScraper(client=http_client),
            explain_scraper=XkcdExplainScraper(client=http_client),
        )

        if not end:
            end = await origin_with_explain_scraper.origin_scraper.fetch_latest_number()

        limits = LimitParams(start, end, chunk_size, delay)

        with base_progress:
            origin_with_explain_data = await origin_with_explain_scraper.fetch_many(
                limits,
                base_progress,
            )

            await upload_origin_with_explanation(
                api_client,
                origin_with_explain_data,
                limits,
                base_progress,
            )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
