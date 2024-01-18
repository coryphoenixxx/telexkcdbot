import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles.os as aos
import filetype
import imagesize
from aiofiles.tempfile import NamedTemporaryFile
from aiohttp import (
    AsyncResolver,
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TCPConnector,
)
from starlette.datastructures import UploadFile

from src.app.images.dtos import ImageObj
from src.app.images.exceptions import (
    RequestFileIsEmptyError,
    UnsupportedImageFormatError,
    UploadExceedLimitError,
)
from src.app.images.types import ImageFormat
from src.core.types import Dimensions


class UnexpectedStatusCodeError(Exception):
    ...


def get_session(timeout: int = 10):
    connector = TCPConnector(
        resolver=AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"]),
        ttl_dns_cache=600,
        ssl=False,
    )
    return ClientSession(connector=connector, timeout=ClientTimeout(timeout))


@asynccontextmanager
async def retry_get(
    session: ClientSession,
    url: str,
    max_tries: int = 3,
    interval: float = 5,
) -> ClientResponse:
    for _ in range(max_tries):
        try:
            async with session.get(url=url) as response:
                status = response.status
                if status == 200:
                    yield response
                    break
                else:
                    logging.warning(f"{url} return invalid status code: {status}.")
                    raise UnexpectedStatusCodeError
        except (TimeoutError, UnexpectedStatusCodeError, ClientConnectorError):
            await asyncio.sleep(interval)
        except Exception:
            await session.close()
            raise
    else:
        logging.error(f"{url} is unavailable after {max_tries} attempts.")


class UploadImageReader:
    _CHUNK_SIZE: int = 1024 * 64

    def __init__(self, tmp_dir: str, upload_max_size: int):
        self._tmp_dir = Path(tmp_dir)
        self._upload_max_size = upload_max_size
        self._supported_formats = tuple(ImageFormat)

    async def read(self, upload: UploadFile | None) -> ImageObj | None:
        if not upload or not upload.filename:
            raise RequestFileIsEmptyError

        tmp_path = await self._read_to_temp(upload)

        return ImageObj(
            path=tmp_path,
            fmt=self._get_real_image_format(tmp_path),
            dimensions=Dimensions(*imagesize.get(tmp_path)),
        )

    async def download(self, session: ClientSession, url: str) -> ImageObj:
        tmp_path = await self._download_to_temp(session, url)

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

    async def _download_to_temp(
        self,
        session: ClientSession,
        url: str,
    ) -> Path:
        await aos.makedirs(self._tmp_dir, exist_ok=True)

        async with retry_get(
            session=session,
            url=url,
        ) as response:
            file_size = 0
            async with NamedTemporaryFile(delete=False, dir=self._tmp_dir) as temp:
                while chunk := await response.content.read(self._CHUNK_SIZE):
                    file_size += len(chunk)
                    if file_size > self._upload_max_size:
                        raise UploadExceedLimitError(upload_max_size=self._upload_max_size)
                    await temp.write(chunk)
            if file_size == 0:
                raise RequestFileIsEmptyError

        return Path(temp.name)

    async def _read_to_temp(self, file: UploadFile) -> Path:
        await aos.makedirs(self._tmp_dir, exist_ok=True)

        async with NamedTemporaryFile(delete=False, dir=self._tmp_dir) as temp:
            file_size = 0
            while chunk := await file.read(self._CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > self._upload_max_size:
                    raise UploadExceedLimitError(upload_max_size=self._upload_max_size)
                await temp.write(chunk)
            if file_size == 0:
                raise RequestFileIsEmptyError

        return Path(temp.name)
