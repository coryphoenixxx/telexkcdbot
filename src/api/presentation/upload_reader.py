import logging
from pathlib import Path
from typing import Final

import aiofiles.os as aos
import filetype
import imagesize
from aiofiles.tempfile import NamedTemporaryFile
from aiohttp import StreamReader
from shared.http_client import HttpClient
from shared.types import ImageFormat
from starlette.datastructures import UploadFile
from yarl import URL

from api.application.exceptions.image import (
    DownloadImageError,
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadExceedLimitError,
)
from api.core.types import Dimensions
from api.presentation.types import ImageObj


class UploadImageHandler:
    _CHUNK_SIZE: Final = 1024 * 64

    def __init__(self, tmp_dir: Path, upload_max_size: int, http_client: HttpClient):
        self._tmp_dir = tmp_dir
        self._upload_max_size = upload_max_size
        self._supported_formats = tuple(ImageFormat)
        self._http_client = http_client

    async def read(self, upload: UploadFile | None) -> ImageObj | None:
        if not upload or not upload.filename:
            raise RequestFileIsEmptyError

        return await self._read_to_temp(upload)

    async def download(self, url: URL | str) -> ImageObj:
        if isinstance(url, str):
            url = URL(url)
        async with self._http_client.safe_get(url=url) as response:  # type: ClientResponse
            if response.status == 200:
                return await self._read_to_temp(response.content)
            else:
                raise DownloadImageError

    async def _read_to_temp(self, obj: StreamReader | UploadFile) -> ImageObj:
        await aos.makedirs(self._tmp_dir, exist_ok=True)

        async with NamedTemporaryFile(delete=False, dir=self._tmp_dir) as temp:
            file_size = 0
            while chunk := await obj.read(self._CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > self._upload_max_size:
                    raise UploadExceedLimitError(upload_max_size=self._upload_max_size)
                await temp.write(chunk)
            if file_size == 0:
                raise RequestFileIsEmptyError

        tmp_path = Path(temp.name)

        return ImageObj(
            path=tmp_path,
            fmt=self._get_real_image_format(tmp_path),
            dimensions=Dimensions(*imagesize.get(tmp_path)),
        )

    def _get_real_image_format(self, path: Path) -> ImageFormat:
        fmt = None
        try:
            extension = filetype.guess_extension(path)
            if extension is None:
                raise ValueError
            fmt = ImageFormat(extension)
        except ValueError:
            raise UnsupportedImageFormatError(
                format=fmt,
                supported_formats=self._supported_formats,
            )
        except FileNotFoundError as err:
            logging.error(f"{err.strerror}: {path}")
            raise err
        else:
            return fmt
