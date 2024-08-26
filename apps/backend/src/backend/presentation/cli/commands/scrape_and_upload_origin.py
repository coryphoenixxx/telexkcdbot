
import click
from dishka import AsyncContainer
from rich.progress import Progress

from backend.application.dtos import ComicRequestDTO, ComicResponseDTO
from backend.application.services import ComicWriteService
from backend.core.value_objects import IssueNumber, TagName
from backend.infrastructure.downloader import Downloader
from backend.infrastructure.utils import cast_or_none
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import XkcdExplainScraper, XkcdOriginScraper
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdOriginWithExplainScrapedData
from backend.infrastructure.xkcd.utils import run_concurrently
from backend.presentation.cli.common import async_command, base_progress, positive_number_callback


async def scrape_origin_with_explain_data(
    origin_scraper: XkcdOriginScraper,
    explain_scraper: XkcdExplainScraper,
    limits: LimitParams,
    progress: Progress,
) -> list[XkcdOriginWithExplainScrapedData]:
    origin_data_list = await origin_scraper.fetch_many(limits, progress)
    explain_data_list = await explain_scraper.fetch_many(limits, progress)

    data = []

    for origin_data, explain_data in zip(
        sorted(origin_data_list, key=lambda d: d.number),
        sorted(explain_data_list, key=lambda d: d.number),
        strict=True,
    ):
        data.append(
            XkcdOriginWithExplainScrapedData(
                number=origin_data.number,
                publication_date=origin_data.publication_date,
                xkcd_url=origin_data.xkcd_url,
                title=origin_data.title,
                tooltip=origin_data.tooltip,
                click_url=origin_data.click_url,
                is_interactive=origin_data.is_interactive,
                image_url=origin_data.image_url,
                explain_url=explain_data.explain_url if explain_data else None,
                tags=explain_data.tags if explain_data else [],
                raw_transcript=explain_data.raw_transcript if explain_data else "",
            )
        )

    return data


async def download_image_and_upload_coro(
    data: XkcdOriginWithExplainScrapedData,
    downloader: Downloader,
    container: AsyncContainer,
) -> ComicResponseDTO:
    temp_image_id = await downloader.download(data.image_url) if data.image_url else None

    async with container() as request_container:
        service: ComicWriteService = await request_container.get(ComicWriteService)
        return await service.create(
            dto=ComicRequestDTO(
                number=IssueNumber(data.number),
                title=data.title,
                publication_date=data.publication_date,
                tooltip=data.tooltip,
                raw_transcript=data.raw_transcript,
                xkcd_url=str(data.xkcd_url),
                explain_url=cast_or_none(str, data.explain_url),
                click_url=cast_or_none(str, data.click_url),
                is_interactive=data.is_interactive,
                tags=[TagName(tag) for tag in data.tags],
                temp_image_id=temp_image_id,
            )
        )


@click.command()
@click.option("--start", type=int, default=1, callback=positive_number_callback)
@click.option("--end", type=int, callback=positive_number_callback)
@click.option("--chunk_size", type=int, default=100, callback=positive_number_callback)
@click.option("--delay", type=float, default=0.01, callback=positive_number_callback)
@click.pass_context
@async_command
async def scrape_and_upload_origin_command(
    ctx: click.Context,
    start: int,
    end: int | None,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta.get("container")

    origin_scraper = await container.get(XkcdOriginScraper)
    explain_scraper = await container.get(XkcdExplainScraper)

    if not end:
        end = await origin_scraper.fetch_latest_number()

    limits = LimitParams(start, end, chunk_size, delay)

    with base_progress:
        origin_with_explain_data = await scrape_origin_with_explain_data(
            origin_scraper=origin_scraper,
            explain_scraper=explain_scraper,
            limits=limits,
            progress=base_progress,
        )
        await run_concurrently(
            data=origin_with_explain_data,
            coro=download_image_and_upload_coro,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                base_progress,
                "Origin data uploading...",
                len(origin_with_explain_data),
            ),
            downloader=await container.get(Downloader),
            container=container,
        )

    await container.close()
