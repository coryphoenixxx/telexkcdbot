import asyncio
import logging
from pathlib import Path

from aiohttp import ClientPayloadError
from shared.http_client import AsyncHttpClient
from shared.my_types import HTTPStatusCodes
from yarl import URL

from api.core.exceptions import DownloadError
from api.infrastructure.filesystem.temp_file_manager import TempFileManager

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(
        self,
        http_client: AsyncHttpClient,
        temp_file_manager: TempFileManager,
        timeout: float,
        attempts: int,
        interval: int,
    ) -> None:
        self._http_client = http_client
        self._temp_file_manager = temp_file_manager
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

    async def _download_job(self, url: URL | str, filename: str) -> Path:
        for _ in range(self._attempts):
            try:
                async with self._http_client.safe_get(url=url) as response:
                    if response.status == HTTPStatusCodes.HTTP_200_OK:
                        return await self._temp_file_manager.read_from_stream(
                            source=response.content,
                            filename=filename,
                        )
            except (TimeoutError, ClientPayloadError):
                await asyncio.sleep(self._interval)
                continue
