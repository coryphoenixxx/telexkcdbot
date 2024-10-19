import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import click
from dishka import AsyncContainer

from backend.application.comic.commands import TranslationCreateCommand
from backend.application.comic.filters import ComicFilters
from backend.application.comic.services import AddTranslationInteractor, ComicReader
from backend.application.common.pagination import Pagination
from backend.application.config import AppConfig
from backend.application.image.services import UploadImageInteractor
from backend.domain.entities import TranslationStatus
from backend.domain.utils import cast_or_none, value_or_none
from backend.domain.value_objects import ImageId, Language, TranslationId
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
        reader: ComicReader = await request_container.get(ComicReader)

        _, comics = await reader.get_list(filters=ComicFilters(), pagination=Pagination())
        if not comics:
            logger.error("There are no comics in the database.")
            raise click.Abort

        for comic in comics:
            if comic.number:
                number_comic_id_map[comic.number] = comic.id

    return number_comic_id_map


async def upload_one_translation(
    data: XkcdTranslationScrapedData,
    number_comic_id_map: dict[int, int],
    container: AsyncContainer,
) -> TranslationId:
    async with container() as request_container:
        image_id: ImageId | None = None
        if data.image_path:
            upload_image_interactor: UploadImageInteractor = await request_container.get(
                UploadImageInteractor
            )
            image_id = await upload_image_interactor.execute(data.image_path)

        add_translation_interactor: AddTranslationInteractor = await request_container.get(
            AddTranslationInteractor
        )
        return await add_translation_interactor.execute(
            command=TranslationCreateCommand(
                comic_id=number_comic_id_map[data.number],
                language=Language(data.language),
                title=data.title,
                tooltip=data.tooltip,
                transcript=data.transcript,
                translator_comment=data.translator_comment,
                source_url=cast_or_none(str, data.source_url),
                status=TranslationStatus.PUBLISHED,
                image_id=value_or_none(image_id),
            ),
        )
