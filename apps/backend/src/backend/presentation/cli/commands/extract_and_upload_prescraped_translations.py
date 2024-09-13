import csv
import errno
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import click
from yarl import URL

from backend.core.value_objects import Language
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData
from backend.presentation.cli.common import (
    async_command,
    clean_up,
    get_number_comic_id_map,
    positive_number,
    upload_one_translation,
)
from backend.presentation.cli.config import CLIConfig
from backend.presentation.cli.progress import ProgressChunkedRunner, base_progress


def extract_prescraped_translations(
    prescraped_zip: Path,
    extract_to: Path,
    filter_numbers: set[int],
) -> list[XkcdTranslationScrapedData]:
    translations = []

    if not prescraped_zip.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), prescraped_zip)

    with ZipFile(prescraped_zip, "r") as f:
        f.extractall(extract_to)

    for lang_code_dir in extract_to.iterdir():
        Language(lang_code_dir.name)
        images_dir = lang_code_dir / "images"

        number_image_path_map = {
            int(image_path.stem): image_path for image_path in images_dir.iterdir()
        }

        csv_data_path = lang_code_dir / "data.csv"
        if not csv_data_path.exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), csv_data_path)

        with csv_data_path.open() as f:
            csv_reader = csv.DictReader(f)

            for row in csv_reader:
                number, title, tooltip, source_url = (
                    int(row["number"]),
                    row["title"],
                    row["tooltip"],
                    URL(url) if (url := row["source_url"]) else None,
                )

                if number not in filter_numbers:
                    continue

                translations.append(
                    XkcdTranslationScrapedData(
                        number=number,
                        source_url=source_url,
                        title=title,
                        tooltip=tooltip,
                        image_path=number_image_path_map[number],
                        language=lang_code_dir.name,
                    )
                )

    return translations


@click.command()
@click.option("--chunk_size", type=int, default=100, callback=positive_number)
@click.option("--delay", type=float, default=0.1, callback=positive_number)
@click.pass_context
@clean_up
@async_command
async def extract_and_upload_prescraped_translations_command(
    ctx: click.Context,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta["container"]

    number_comic_id_map = await get_number_comic_id_map(container)
    db_numbers = set(number_comic_id_map.keys())

    cli_config: CLIConfig = await container.get(CLIConfig)

    with TemporaryDirectory() as temp_dir:
        try:
            prescraped_translations = extract_prescraped_translations(
                prescraped_zip=cli_config.prescraped_dir / "prescraped_translations.zip",
                extract_to=Path(temp_dir),
                filter_numbers=db_numbers,
            )
        except FileNotFoundError as err:
            raise click.FileError(filename=err.filename, hint="File not found.") from None

        with base_progress:
            await ProgressChunkedRunner(base_progress, chunk_size, delay).run(
                desc="Prescraped translations uploading:",
                coro=upload_one_translation,
                data=prescraped_translations,
                number_comic_id_map=number_comic_id_map,
                container=container,
            )
