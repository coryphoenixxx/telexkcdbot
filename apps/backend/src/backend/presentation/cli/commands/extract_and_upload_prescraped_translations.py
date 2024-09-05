import csv
import errno
import importlib.resources
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import click
from dishka import AsyncContainer
from yarl import URL

from backend.application.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.services.comic import ComicReadService, ComicWriteService
from backend.core.value_objects import ComicID, Language
from backend.infrastructure.upload_image_manager import UploadImageManager
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdTranslationZippedData
from backend.infrastructure.xkcd.utils import run_concurrently
from backend.presentation.cli.common import (
    DatabaseIsEmptyError,
    async_command,
    base_progress,
    positive_number_callback,
)

logger = logging.getLogger(__name__)


def extract_prescraped_translations(
    zip_path: Path,
    extract_to: Path,
    limits: LimitParams,
    pbar: CustomProgressBar | None,
) -> list[XkcdTranslationZippedData]:
    translations = []

    with ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

    for lang_code_dirname in os.listdir(extract_to):
        root = Path(extract_to) / lang_code_dirname
        images_dir = root / "images"

        number_image_path_map = {}
        for image_name in os.listdir(images_dir):
            abs_image_path = images_dir / image_name

            if not abs_image_path.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), abs_image_path)

            number_image_path_map[int(image_name.split(".")[0])] = abs_image_path

        with Path(root / "data.csv").open() as data_file:
            csv_reader = csv.DictReader(data_file)

            for row in csv_reader:
                number = int(row["number"])

                if number < limits.start or number > limits.end:
                    continue

                source_url = row["source_url"]

                translations.append(
                    XkcdTranslationZippedData(
                        number=number,
                        source_url=URL(source_url) if source_url else None,
                        title=row["title"],
                        tooltip=row["tooltip"],
                        image_path=number_image_path_map[number],
                        language=lang_code_dirname,
                    ),
                )

                if pbar:
                    pbar.advance()

    if pbar:
        pbar.finish()

    return translations


async def copy_image_and_upload_coro(
    data: XkcdTranslationZippedData,
    number_comic_id_map: dict[int, int],
    container: AsyncContainer,
) -> TranslationResponseDTO:
    upload_image_manager = await container.get(UploadImageManager)

    temp_image_id = None
    if data.image_path:
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
async def extract_and_upload_prescraped_translations_command(
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

    with base_progress, TemporaryDirectory() as temp_dir:
        with importlib.resources.path("assets", "prescraped_translations.zip") as path:
            try:
                prescraped_translations = extract_prescraped_translations(
                    zip_path=path,
                    extract_to=Path(temp_dir),
                    limits=limits,
                    pbar=CustomProgressBar(base_progress, "Extracting prescraped translations..."),
                )
            except FileNotFoundError as err:
                logger.warning(
                    "File not found: %s. Skip prescraped translations extraction...", err.filename
                )

        await run_concurrently(
            data=prescraped_translations,
            coro=copy_image_and_upload_coro,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                base_progress,
                "Translations uploading...",
                len(prescraped_translations),
            ),
            number_comic_id_map=number_comic_id_map,
            container=container,
        )
