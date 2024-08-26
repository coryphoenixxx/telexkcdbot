import logging.config
import random
from typing import TypeVar

import click
from dishka import AsyncContainer

from backend.application.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.services.comic import ComicReadService, ComicWriteService
from backend.core.value_objects import ComicID, Language
from backend.infrastructure.downloader import Downloader
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
    downloader: Downloader,
    container: AsyncContainer,
) -> TranslationResponseDTO:
    temp_image_id = await downloader.download(data.image_url) if data.image_url else None

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
@click.option("--delay", type=float, default=0.01, callback=positive_number_callback)
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

    ru_scraper = await container.get(XkcdRUScraper)
    de_scraper = await container.get(XkcdDEScraper)
    es_scraper = await container.get(XkcdESScraper)
    zh_scraper = await container.get(XkcdZHScraper)
    fr_scraper = await container.get(XkcdFRScraper)

    with base_progress:
        scraped_translations = []
        for scraper in (ru_scraper, de_scraper, es_scraper, zh_scraper, fr_scraper):
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
            downloader=await container.get(Downloader),
            container=container,
        )
