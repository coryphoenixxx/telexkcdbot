import asyncio
import csv
import errno
import logging.config
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import uvloop
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from scraper.dtos import XkcdOriginWithExplainScrapedData, XkcdTranslationData
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
from shared.types import LanguageCode
from shared.utils import flatten
from yarl import URL

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
        "rich": {
            "class": "rich.logging.RichHandler",
            "level": "NOTSET",
            "formatter": None,
        },
    },
    "loggers": {
        "root": {
            "handlers": ["default", "rich"],
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
    translation_data: list[XkcdTranslationData],
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


def extract_prescraped_translations(
    extract_to: Path,
    pbar: ProgressBar | None,
    zip_path: Path = Path.cwd() / "prescraped_translations.zip",
) -> list[XkcdTranslationData]:
    translations = []

    with ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

        for lang_code_dir in os.listdir(Path(extract_to)):
            root = Path(extract_to) / lang_code_dir
            images_dir = root / "images"

            number_image_path_map = {}
            for image_name in os.listdir(images_dir):
                image_path = images_dir / image_name

                if not image_path.exists():
                    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), image_path)

                number_image_path_map[int(image_name.split(".")[0])] = image_path

            with open(root / "data.csv") as data_file:
                csv_reader = csv.DictReader(data_file)

                for row in csv_reader:
                    number = int(row["number"])
                    source_link = row["source_link"]
                    tooltip = row["tooltip"]

                    translations.append(
                        XkcdTranslationData(
                            number=number,
                            source_link=URL(source_link) if source_link else None,
                            title=row["title"],
                            tooltip=tooltip if tooltip else None,
                            image=number_image_path_map[number],
                            language=LanguageCode(lang_code_dir),
                        ),
                    )

                    if pbar:
                        pbar.advance()

    if pbar:
        pbar.finish()

    return translations


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
                    tg.create_task(XkcdRUScraper(client=http_client).fetch_many(limits, progress)),
                    tg.create_task(XkcdDEScraper(client=http_client).fetch_many(limits, progress)),
                    tg.create_task(XkcdESScraper(client=http_client).fetch_many(limits, progress)),
                    tg.create_task(XkcdCNScraper(client=http_client).fetch_many(limits, progress)),
                    tg.create_task(XkcdFRScraper(client=http_client).fetch_many(limits, progress)),
                ]

            translations = flatten([task.result() for task in tasks])

            with TemporaryDirectory(dir=".") as temp_dir:
                try:
                    prescraped_translations = extract_prescraped_translations(
                        extract_to=Path(temp_dir),
                        pbar=ProgressBar(progress, "Extracting prescraped translations..."),
                    )
                except FileNotFoundError as err:
                    logger.error(f"File not found: {err.filename}")
                else:
                    translations.extend(prescraped_translations)

                number_comic_id_map = await upload_origin_with_explanation(
                    api_client,
                    origin_with_explanation,
                    limits,
                    progress,
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
