import asyncio
from dataclasses import dataclass
from pathlib import Path

from aiohttp import ClientPayloadError
from yarl import URL

from backend.core.value_objects import TempFileID
from backend.infrastructure.filesystem import TempFileManager
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.http_client.http_codes import HTTPStatusCodes


@dataclass(slots=True)
class DownloadError(Exception):
    url: str
    attempts: int
    interval: float

    @property
    def message(self) -> str:
        return (
            f"Couldn't download the file "
            f"(url={self.url}, attempts={self.attempts}, interval={self.interval})."
        )


@dataclass(slots=True)
class Downloader:
    http_client: AsyncHttpClient
    temp_file_manager: TempFileManager
    attempts: int = 3
    interval: float = 0.1
    chunk_size: int = 64 * 1024

    async def download(self, url: URL) -> Path:
        for _ in range(self.attempts):
            if temp_file_id := await self._download_attempt(url):
                return self.temp_file_manager.get_abs_path(temp_file_id)
            await asyncio.sleep(self.interval)
        raise DownloadError(str(url), self.attempts, self.interval)

    async def _download_attempt(self, url: URL) -> TempFileID | None:
        try:
            async with self.http_client.safe_get(url=url) as response:
                if response.status == HTTPStatusCodes.OK_200:
                    return await self.temp_file_manager.read_from_stream(
                        stream=response.content,
                        chunk_size=self.chunk_size,
                    )
                return None
        except (TimeoutError, ClientPayloadError):
            return None
