import asyncio
import logging
from pathlib import Path
from uuid import uuid4

import filetype
from aiohttp import ClientPayloadError
from pydantic import HttpUrl
from shared.http_client import AsyncHttpClient
from shared.my_types import HTTPStatusCodes, ImageFormat
from starlette.datastructures import UploadFile
from yarl import URL

from api.core.exceptions import (
    DownloadError,
    UnsupportedImageFormatError,
    UploadedImageConflictError,
    UploadedImageIsNotExistsError,
)
from api.core.value_objects import TempImageID
from api.infrastructure.filesystem.image_file_manager import ImageFileManager

logger = logging.getLogger(__name__)


class ImageValidator:
    def __init__(self, supported_formats: tuple[ImageFormat, ...]) -> None:
        self._supported_formats = supported_formats

    def validate_format(self, path: Path) -> None:
        extension = filetype.guess_extension(path)

        if extension not in self._supported_formats:
            raise UnsupportedImageFormatError(
                format=extension,
                supported_formats=tuple(ImageFormat),
            )


class Downloader:
    def __init__(
        self,
        http_client: AsyncHttpClient,
        file_manager: ImageFileManager,
        timeout: float,
        attempts: int,
        interval: int,
    ) -> None:
        self._http_client = http_client
        self._file_manager = file_manager
        self._timeout = timeout
        self._attempts = attempts
        self._interval = interval

    async def download(self, url: URL | str, save_to: str) -> Path:
        try:
            path = await asyncio.wait_for(
                fut=self._download_job(url, save_to),
                timeout=self._timeout,
            )
        except TimeoutError:
            logger.exception("Couldn't download %s after %s seconds.", url, self._timeout)
        else:
            return path

        raise DownloadError(str(url))

    async def _download_job(self, url: URL | str, save_to: str) -> Path:
        for _ in range(self._attempts):
            try:
                async with self._http_client.safe_get(url=url) as response:
                    if response.status == HTTPStatusCodes.HTTP_200_OK:
                        return await self._file_manager.read_to_temp(response.content, save_to)
            except (TimeoutError, ClientPayloadError):
                await asyncio.sleep(self._interval)
                continue


class UploadImageManager:
    def __init__(
        self,
        file_manager: ImageFileManager,
        downloader: Downloader,
        validator: ImageValidator,
    ) -> None:
        self._file_manager = file_manager
        self._downloader = downloader
        self._validator = validator

    async def read(self, file: UploadFile | None, url: HttpUrl | None) -> TempImageID:
        if file and url:
            raise UploadedImageConflictError

        if (file is None or file.filename is None) and url is None:
            raise UploadedImageIsNotExistsError

        image_id = TempImageID(uuid4())
        temp_filename = str(image_id)

        try:
            image_path = (
                await self._file_manager.read_to_temp(file, temp_filename)
                if file
                else await self._downloader.download(str(url), temp_filename)
            )

            self._validator.validate_format(image_path)
        except Exception:
            await self._file_manager.remove_temp_by_id(image_id)
            raise
        else:
            return image_id
