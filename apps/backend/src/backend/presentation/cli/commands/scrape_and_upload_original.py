from datetime import datetime as dt
from logging import getLogger

import click
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.application.comic.dtos import ComicRequestDTO, ComicResponseDTO
from backend.application.comic.services import ComicReader, CreateComicInteractor
from backend.application.upload.upload_image_manager import UploadImageManager
from backend.application.utils import cast_or_none
from backend.core.value_objects import IssueNumber, TagName
from backend.infrastructure.database.main import check_db_connection
from backend.infrastructure.xkcd import (
    XkcdExplainScraper,
    XkcdOriginalScraper,
)
from backend.infrastructure.xkcd.dtos import (
    XkcdExplainScrapedData,
    XkcdOriginalScrapedData,
)
from backend.presentation.cli.common import (
    async_command,
    clean_up,
    positive_number,
)
from backend.presentation.cli.progress import ProgressChunkedRunner, progress_factory

logger = getLogger(__name__)


async def calc_numbers(start: int, end: int | None, container: AsyncContainer) -> list[int]:
    if end is None:
        original_scraper: XkcdOriginalScraper = await container.get(XkcdOriginalScraper)
        end = await original_scraper.fetch_latest_number()

    if start > end:
        raise click.BadParameter(f"`start` (={start}) must be <= `end` (={end})")

    return list(range(start, end + 1))


async def check_db(container: AsyncContainer) -> None:
    engine = await container.get(AsyncEngine)
    try:
        await check_db_connection(engine)
    except OSError as err:
        logger.exception("Database connection failed: %s", err.strerror)
        raise click.Abort from None

    async with container() as request_container:
        service = await request_container.get(ComicReader)
        latest = await service.get_latest_issue_number()

        if latest:
            logger.error("The database already contains some comics.")
            raise click.Abort


async def upload_one(
    data: tuple[XkcdOriginalScrapedData, XkcdExplainScrapedData],
    container: AsyncContainer,
) -> ComicResponseDTO:
    original_data, explain = data
    temp_image_id = None
    if original_data.image_path:
        upload_image_manager = await container.get(UploadImageManager)
        temp_image_id = upload_image_manager.read_from_file(original_data.image_path)

    async with container() as request_container:
        service: CreateComicInteractor = await request_container.get(CreateComicInteractor)
        return await service.execute(
            dto=ComicRequestDTO(
                number=IssueNumber(original_data.number),
                title=original_data.title,
                publication_date=dt.strptime(  # noqa: DTZ007
                    original_data.publication_date, "%Y-%m-%d"
                ).date(),
                tooltip=original_data.tooltip,
                raw_transcript=explain.raw_transcript,
                xkcd_url=str(original_data.xkcd_url),
                explain_url=cast_or_none(str, explain.explain_url),
                click_url=cast_or_none(str, original_data.click_url),
                is_interactive=original_data.is_interactive,
                tags=[TagName(tag) for tag in explain.tags],
                temp_image_id=temp_image_id,
            )
        )


@click.command()
@click.option("--start", type=int, default=1, callback=positive_number)
@click.option("--end", type=int, callback=positive_number)
@click.option("--chunk_size", type=int, default=100, callback=positive_number)
@click.option("--delay", type=float, default=0.1, callback=positive_number)
@click.pass_context
@clean_up
@async_command
async def scrape_and_upload_original_command(
    ctx: click.Context,
    start: int,
    end: int | None,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta["container"]

    await check_db(container)
    numbers = await calc_numbers(start, end, container)

    original_scraper: XkcdOriginalScraper = await container.get(XkcdOriginalScraper)
    explain_scraper: XkcdExplainScraper = await container.get(XkcdExplainScraper)

    with progress_factory() as progress:
        runner = ProgressChunkedRunner(progress, chunk_size, delay)

        original_data_list = await runner.run(
            desc=f"Original data scraping ({original_scraper.BASE_URL}):",
            coro=original_scraper.fetch_one,
            data=numbers,
        )

        explain_data_list = await runner.run(
            desc=f"Explain data scraping ({explain_scraper.BASE_URL}):",
            coro=explain_scraper.fetch_one,
            data=numbers,
        )

        await runner.run(
            desc="Original data uploading:",
            coro=upload_one,
            data=list(
                zip(
                    sorted(original_data_list, key=lambda d: d.number),
                    sorted(explain_data_list, key=lambda d: d.number),
                    strict=True,
                )
            ),
            container=container,
        )
