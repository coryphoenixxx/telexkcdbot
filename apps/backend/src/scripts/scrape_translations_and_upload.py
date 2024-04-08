import asyncio
import csv
import errno
import logging.config
import os
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import asyncclick as click
import uvloop
from rich.progress import (
    Progress,
)
from scraper.dtos import XkcdTranslationData
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
from scripts.common import positive_number_callback
from scripts.common import progress as base_progress
from shared.api_rest_client import APIRESTClient
from shared.http_client import AsyncHttpClient
from shared.utils import flatten
from yarl import URL

logger = logging.getLogger(__name__)


def extract_prescraped_translations(
    extract_to: Path,
    limits: LimitParams,
    pbar: ProgressBar | None,
    zip_path: Path = Path(__file__).parent / "prescraped_translations.zip",
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

                    if number < limits.start or number > limits.end:
                        continue

                    source_link = row["source_link"]
                    tooltip = row["tooltip"]

                    translations.append(
                        XkcdTranslationData(
                            number=number,
                            source_link=URL(source_link) if source_link else None,
                            title=row["title"],
                            tooltip=tooltip if tooltip else None,
                            image=number_image_path_map[number],
                            language=lang_code_dir,
                        ),
                    )

                    if pbar:
                        pbar.advance()

    if pbar:
        pbar.finish()

    return translations


async def fetch_all_translations(
    http_client: AsyncHttpClient,
    limits: LimitParams,
    progress: Progress,
    temp_dir,
) -> list[XkcdTranslationData]:
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(XkcdRUScraper(client=http_client).fetch_many(limits, progress)),
            tg.create_task(XkcdDEScraper(client=http_client).fetch_many(limits, progress)),
            tg.create_task(XkcdESScraper(client=http_client).fetch_many(limits, progress)),
            tg.create_task(XkcdCNScraper(client=http_client).fetch_many(limits, progress)),
            tg.create_task(XkcdFRScraper(client=http_client).fetch_many(limits, progress)),
        ]

    translations = flatten([task.result() for task in tasks])

    try:
        prescraped_translations = extract_prescraped_translations(
            extract_to=Path(temp_dir),
            pbar=ProgressBar(progress, "Extracting prescraped translations..."),
            limits=limits,
        )
    except FileNotFoundError as err:
        logger.warning(
            f"File not found: {err.filename}. Skip prescraped translations extraction...",
        )
    else:
        translations.extend(prescraped_translations)

    return translations


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
        chunk_size=limits.chunk_size,
        delay=limits.delay,
        pbar=ProgressBar(progress, "Translations uploading...", len(translation_data)),
        number_comic_id_map=number_comic_id_map,
    )


async def get_number_comic_id_map(api_client: APIRESTClient) -> dict[int, int]:
    d = {}
    data = (await api_client.get_comics())["data"]
    for comic in data:
        d[comic["number"]] = comic["id"]

    return d


@click.command()
@click.option("--start", type=int, default=1, callback=positive_number_callback)
@click.option("--end", type=int, callback=positive_number_callback)
@click.option("--chunk_size", type=int, default=100, callback=positive_number_callback)
@click.option("--delay", type=float, default=0.01, callback=positive_number_callback)
@click.option("--api-url", type=str, default="http://127.0.0.1:8000/api")
async def main(start: int, end: int | None, chunk_size: int, delay: int, api_url: str):
    async with AsyncHttpClient() as http_client:
        api_client = APIRESTClient(api_url, http_client)

        if not await api_client.healthcheck():
            return

        number_comic_id_map = await get_number_comic_id_map(api_client)

        if not number_comic_id_map:
            print("Looks like database is empty.")
            return

        origin_with_explain_scraper = XkcdOriginWithExplainDataScraper(
            origin_scraper=XkcdOriginScraper(client=http_client),
            explain_scraper=XkcdExplainScraper(client=http_client),
        )

        if not end:
            end = await origin_with_explain_scraper.origin_scraper.fetch_latest_number()

        limits = LimitParams(start, end, chunk_size, delay)

        with base_progress, TemporaryDirectory(dir="") as temp_dir:
            translations = await fetch_all_translations(
                http_client,
                limits,
                base_progress,
                temp_dir,
            )

            random.shuffle(translations)  # prevent DDOS when loading images via API

            await upload_translations(
                api_client,
                number_comic_id_map,
                translations,
                limits,
                base_progress,
            )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
