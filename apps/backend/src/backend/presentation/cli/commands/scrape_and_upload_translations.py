import logging.config
import random
from typing import TypeVar

import click
from dishka import AsyncContainer

from backend.application.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.services.comic import ComicReadService, ComicWriteService
from backend.core.value_objects import ComicID, Language
from backend.infrastructure.downloader import Downloader
from backend.infrastructure.upload_image_manager import UploadImageManager
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

T = TypeVar("T")


def flatten(matrix: list[list["T"]]) -> list["T"]:
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list


async def download_image_and_upload_coro(
    data: XkcdTranslationScrapedData,
    number_comic_id_map: dict[int, int],
    container: AsyncContainer,
) -> TranslationResponseDTO:
    temp_image_id = None
    if data.image_url:
        downloader = await container.get(Downloader)
        upload_image_manager = await container.get(UploadImageManager)
        temp_image_path = await downloader.download(data.image_url)
        temp_image_id = upload_image_manager.read_from_file(temp_image_path)

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
                source_url=str(data.source_url),
                temp_image_id=temp_image_id,
                is_draft=False,
            ),
        )


@click.command()
@click.option("--chunk_size", type=int, default=100, callback=positive_number_callback)
@click.option("--delay", type=float, default=0.5, callback=positive_number_callback)
@click.pass_context
@async_command
async def scrape_and_upload_translations_command(
    ctx: click.Context,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta.get("container")

    number_comic_id_map = {}

    async with container() as request_container:
        service: ComicReadService = await request_container.get(ComicReadService)
        _, comics = await service.get_list()
        for comic in comics:
            number_comic_id_map[comic.number] = comic.id

        if not number_comic_id_map:
            raise DatabaseIsEmptyError("Looks like database is empty.")

    db_numbers = sorted(number_comic_id_map.keys())

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
