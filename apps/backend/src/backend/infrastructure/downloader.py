import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from aiohttp import ClientPayloadError
from yarl import URL

from backend.core.value_objects import TempFileID
from backend.infrastructure.filesystem.temp_file_manager import TempFileManager
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.http_client.dtos import HTTPStatusCodes

logger = logging.getLogger(__name__)


@dataclass
class DownloadError(Exception):
    url: str

    @property
    def message(self) -> str:
        return f"Couldn't download the image from {self.url}"


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

    async def download(self, url: URL | str) -> Path:
        try:
            temp_image_id = await asyncio.wait_for(
                fut=self._download_job(url),
                timeout=self._timeout,
            )
        except TimeoutError:
            logger.exception("Couldn't download %s after %s seconds.", url, self._timeout)
        else:
            return self._temp_file_manager.get_abs_path_by_id(temp_image_id)

    async def _download_job(self, url: URL | str) -> TempFileID | None:
        for _ in range(self._attempts):
            try:
                async with self._http_client.safe_get(url=url) as response:
                    if response.status == HTTPStatusCodes.OK_200:
                        return await self._temp_file_manager.read_from_stream(
                            stream=response.content,
                            chunk_size=1024 * 64,
                        )
            except (TimeoutError, ClientPayloadError):
                await asyncio.sleep(self._interval)
                continue
        raise DownloadError(str(url))
