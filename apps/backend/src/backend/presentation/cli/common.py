import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import click
from dishka import AsyncContainer

from backend.application.comic.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.comic.services import AddTranslationInteractor, ComicReader
from backend.application.common.pagination import ComicFilterParams
from backend.application.config import AppConfig
from backend.application.upload.upload_image_manager import UploadImageManager
from backend.application.utils import cast_or_none
from backend.core.value_objects import ComicID, Language
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData

logger = logging.getLogger(__name__)


def positive_number(_: click.Context, __: click.core.Option, value: int) -> int | None:
    if not value:
        return None
    if isinstance(value, int | float) and value > 0:
        return value
    raise click.BadParameter("parameter must be positive")


def async_command(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def clean_temp_dir(temp_dir: Path) -> None:
    for f in temp_dir.iterdir():
        if not f.name.startswith("."):
            f.unlink()


def clean_up(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = args[0]
        try:
            return f(*args, **kwargs)
        except BaseException:
            container = ctx.meta["container"]
            config: AppConfig = asyncio.run(container.get(AppConfig))
            clean_temp_dir(temp_dir=config.temp_dir)
            raise

    return wrapper


async def get_number_comic_id_map(container: AsyncContainer) -> dict[int, int]:
    number_comic_id_map = {}

    async with container() as request_container:
        service: ComicReader = await request_container.get(ComicReader)

        _, comics = await service.get_list(query_params=ComicFilterParams())
        for comic in comics:
            if comic.number:
                number_comic_id_map[comic.number.value] = comic.id.value

        if not number_comic_id_map:
            logger.error("There are no comics in the database.")
            raise click.Abort

    return number_comic_id_map


async def upload_one_translation(
    data: XkcdTranslationScrapedData,
    number_comic_id_map: dict[int, int],
    container: AsyncContainer,
) -> TranslationResponseDTO:
    upload_image_manager = await container.get(UploadImageManager)
    temp_image_id = upload_image_manager.read_from_file(data.image_path)

    async with container() as request_container:
        service: AddTranslationInteractor = await request_container.get(AddTranslationInteractor)
        return await service.execute(
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
