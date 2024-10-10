from collections.abc import Sequence
from datetime import datetime as dt
from logging import getLogger

import click
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.application.comic.commands import ComicCreateCommand, TagCreateCommand
from backend.application.comic.services import (
    ComicReader,
    CreateComicInteractor,
    CreateManyTagsInteractor,
)
from backend.application.image.services import UploadImageInteractor
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import ComicId, TagId
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
        reader = await request_container.get(ComicReader)
        latest = await reader.get_latest_issue_number()

        if latest:
            logger.error("Database already contains some comics.")
            raise click.Abort


async def upload_one(
    data: tuple[XkcdOriginalScrapedData, XkcdExplainScrapedData],
    container: AsyncContainer,
) -> ComicId:
    original_data, explain_data = data

    async with container() as request_container:
        image_ids = []
        if original_data.image_path:
            upload_image_interactor: UploadImageInteractor = await request_container.get(
                UploadImageInteractor
            )
            image_id = await upload_image_interactor.execute(original_data.image_path)
            image_ids.append(image_id.value)

        tag_ids: Sequence[TagId] = []
        if explain_data.tags:
            create_many_tags_interactor: CreateManyTagsInteractor = await request_container.get(
                CreateManyTagsInteractor
            )

            tag_ids = await create_many_tags_interactor.execute(
                commands=[
                    TagCreateCommand(
                        name=name,
                        is_visible=True,
                        from_explainxkcd=True,
                    )
                    for name in explain_data.tags
                ]
            )

        create_comic_interactor: CreateComicInteractor = await request_container.get(
            CreateComicInteractor
        )
        return await create_comic_interactor.execute(
            command=ComicCreateCommand(
                number=original_data.number,
                title=original_data.title,
                publication_date=dt.strptime(  # noqa: DTZ007
                    original_data.publication_date, "%Y-%m-%d"
                ).date(),
                tooltip=original_data.tooltip,
                transcript=explain_data.transcript,
                xkcd_url=str(original_data.xkcd_url),
                explain_url=cast_or_none(str, explain_data.explain_url),
                click_url=cast_or_none(str, original_data.click_url),
                is_interactive=original_data.is_interactive,
                tag_ids=[tag_id.value for tag_id in tag_ids],
                image_ids=image_ids,
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

        explain_runner = ProgressChunkedRunner(progress, chunk_size // 4, delay * 10)

        explain_data_list = await explain_runner.run(
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
