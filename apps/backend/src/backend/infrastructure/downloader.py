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


@dataclass(slots=True)
class DownloadError(Exception):
    url: str
    attempts: int
    interval: float

    @property
    def message(self) -> str:
        return f"Couldn't download the file from {self.url}"


class Downloader:
    def __init__(
        self,
        http_client: AsyncHttpClient,
        temp_file_manager: TempFileManager,
        attempts: int = 3,
        interval: float = 0.5,
        chunk_size: int = 64 * 1024,
    ) -> None:
        self._http_client = http_client
        self._temp_file_manager = temp_file_manager
        self._attempts = attempts
        self._interval = interval
        self._chunk_size = chunk_size

    async def download(self, url: URL) -> Path:
        for _ in range(self._attempts):
            if temp_file_id := await self._download_attempt(url):
                return self._temp_file_manager.get_abs_path_by_id(temp_file_id)
            await asyncio.sleep(self._interval)
        raise DownloadError(str(url), self._attempts, self._interval)

    async def _download_attempt(self, url: URL) -> TempFileID | None:
        try:
            async with self._http_client.safe_get(url=url) as response:
                if response.status == HTTPStatusCodes.OK_200:
                    return await self._temp_file_manager.read_from_stream(
                        stream=response.content,
                        chunk_size=self._chunk_size,
                    )
                return None
        except (TimeoutError, ClientPayloadError):
            return None
