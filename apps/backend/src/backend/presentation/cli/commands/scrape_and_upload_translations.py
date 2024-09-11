import logging.config
import random

import click
from dishka import AsyncContainer

from backend.application.comic.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.comic.services import ComicReadService, ComicWriteService
from backend.application.common.pagination import ComicFilterParams
from backend.application.upload.upload_image_manager import UploadImageManager
from backend.application.utils import cast_or_none
from backend.core.value_objects import ComicID, Language
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import (
    XkcdDEScraper,
    XkcdESScraper,
    XkcdFRScraper,
    XkcdRUScraper,
    XkcdZHScraper,
)
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdTranslationScrapedData
from backend.infrastructure.xkcd.utils import run_concurrently
from backend.presentation.cli.common import (
    DatabaseIsEmptyError,
    async_command,
    base_progress,
    positive_number_callback,
)

logger = logging.getLogger(__name__)


async def download_image_and_upload_coro(
    data: XkcdTranslationScrapedData,
    number_comic_id_map: dict[int, int],
    container: AsyncContainer,
) -> TranslationResponseDTO:
    upload_image_manager = await container.get(UploadImageManager)
    temp_image_id = upload_image_manager.read_from_file(data.image_path)

    async with container() as request_container:
        service: ComicWriteService = await request_container.get(ComicWriteService)
        return await service.add_translation(
            comic_id=ComicID(number_comic_id_map[data.number]),
            dto=TranslationRequestDTO(
                language=Language(data.language),
                title=data.title,
                tooltip=data.tooltip,
                raw_transcript=data.raw_transcript,
                translator_comment=data.translator_comment,
                source_url=cast_or_none(str, data.source_url),
                temp_image_id=temp_image_id,
                is_draft=False,
            ),
        )


@click.command()
@click.option("--chunk_size", type=int, default=100, callback=positive_number_callback)
@click.option("--delay", type=float, default=3, callback=positive_number_callback)
@click.pass_context
@async_command
async def scrape_and_upload_translations_command(
    ctx: click.Context,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta["container"]

    number_comic_id_map = {}

    async with container() as request_container:
        service: ComicReadService = await request_container.get(ComicReadService)
        _, comics = await service.get_list(query_params=ComicFilterParams())
        for comic in comics:
            if comic.number:
                number_comic_id_map[comic.number.value] = comic.id.value

        if not number_comic_id_map:
            raise DatabaseIsEmptyError("Looks like database is empty.")

    db_numbers = sorted(number_comic_id_map.values())

    limits = LimitParams(
        start=db_numbers[0],
        end=db_numbers[-1],
        chunk_size=chunk_size,
        delay=delay,
    )

    with base_progress:
        scraped_translations = []
        for scraper_type in (
            XkcdRUScraper,
            XkcdDEScraper,
            XkcdESScraper,
            XkcdZHScraper,
            XkcdFRScraper,
        ):
            scraper = await container.get(scraper_type)
            scraped_translations.extend(await scraper.fetch_many(limits, base_progress))

        random.shuffle(scraped_translations)  # reduce DDOS when downloading images

        await run_concurrently(
            data=scraped_translations,
            coro=download_image_and_upload_coro,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                base_progress,
                "Translations uploading...",
                len(scraped_translations),
            ),
            number_comic_id_map=number_comic_id_map,
            container=container,
        )
