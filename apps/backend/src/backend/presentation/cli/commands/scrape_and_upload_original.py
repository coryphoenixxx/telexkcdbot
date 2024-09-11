from datetime import datetime as dt

import click
from dishka import AsyncContainer
from rich.progress import Progress

from backend.application.dtos import ComicRequestDTO, ComicResponseDTO
from backend.application.services import ComicReadService, ComicWriteService
from backend.core.value_objects import IssueNumber, TagName
from backend.infrastructure.upload_image_manager import UploadImageManager
from backend.infrastructure.utils import cast_or_none
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import XkcdExplainScraper, XkcdOriginalScraper
from backend.infrastructure.xkcd.scrapers.dtos import (
    LimitParams,
    XkcdOriginalWithExplainScrapedData,
)
from backend.infrastructure.xkcd.utils import run_concurrently
from backend.presentation.cli.common import (
    DatabaseIsNotEmptyError,
    async_command,
    base_progress,
    positive_number_callback,
)


async def scrape_original_with_explain_data(
    original_scraper: XkcdOriginalScraper,
    explain_scraper: XkcdExplainScraper,
    limits: LimitParams,
    progress: Progress,
) -> list[XkcdOriginalWithExplainScrapedData]:
    original_data_list = await original_scraper.fetch_many(limits, progress)
    explain_data_list = await explain_scraper.fetch_many(limits, progress)

    data = []

    for original_data, explain_data in zip(
        sorted(original_data_list, key=lambda d: d.number),
        sorted(explain_data_list, key=lambda d: d.number),
        strict=True,
    ):
        data.append(
            XkcdOriginalWithExplainScrapedData(
                number=original_data.number,
                publication_date=original_data.publication_date,
                xkcd_url=original_data.xkcd_url,
                title=original_data.title,
                tooltip=original_data.tooltip,
                click_url=original_data.click_url,
                is_interactive=original_data.is_interactive,
                image_path=original_data.image_path,
                explain_url=explain_data.explain_url,
                tags=explain_data.tags,
                raw_transcript=explain_data.raw_transcript,
            )
        )

    return data


async def download_image_and_upload_coro(
    data: XkcdOriginalWithExplainScrapedData,
    container: AsyncContainer,
) -> ComicResponseDTO:
    temp_image_id = None
    if data.image_path:
        upload_image_manager = await container.get(UploadImageManager)
        temp_image_id = upload_image_manager.read_from_file(data.image_path)

    async with container() as request_container:
        service: ComicWriteService = await request_container.get(ComicWriteService)
        return await service.create(
            dto=ComicRequestDTO(
                number=IssueNumber(data.number),
                title=data.title,
                publication_date=dt.strptime(  # noqa: DTZ007
                    data.publication_date, "%Y-%m-%d"
                ).date(),
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
@click.option("--delay", type=float, default=3, callback=positive_number_callback)
@click.pass_context
@async_command
async def scrape_and_upload_original_command(
    ctx: click.Context,
    start: int,
    end: int | None,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta["container"]

    original_scraper: XkcdOriginalScraper = await container.get(XkcdOriginalScraper)
    explain_scraper: XkcdExplainScraper = await container.get(XkcdExplainScraper)
    if end is None:
        end = await original_scraper.fetch_latest_number()

    limits = LimitParams(start, end, chunk_size, delay)

    async with container() as request_container:
        service = await request_container.get(ComicReadService)
        latest = await service.get_latest_issue_number()

        if latest:
            raise DatabaseIsNotEmptyError("Looks like database is not empty.")

    with base_progress:
        original_with_explain_data = await scrape_original_with_explain_data(
            original_scraper=original_scraper,
            explain_scraper=explain_scraper,
            limits=limits,
            progress=base_progress,
        )
        await run_concurrently(
            data=original_with_explain_data,
            coro=download_image_and_upload_coro,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                base_progress,
                "Original data uploading...",
                len(original_with_explain_data),
            ),
            container=container,
        )

    await container.close()
