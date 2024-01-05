import asyncio
import time
from pathlib import Path

import aiofiles.os as aos

from src.core.utils import run_every


class Cleaner:
    _CLEANER_SLEEP_SEC = 60 * 5
    _CLEAN_AFTER_SEC = 60

    def __init__(self, tmp_dir: str):
        self._tmp_dir = Path(tmp_dir)
        self._tasks: list[asyncio.Task] = []

    async def run(self):
        await aos.makedirs(self._tmp_dir, exist_ok=True)
        self._tasks.append(asyncio.create_task(
            coro=run_every(self._CLEANER_SLEEP_SEC, self._clean_tmp_dir_task),
            name="CleanTempDir_Task",
        ))

    async def stop(self):
        for task in self._tasks:
            task.cancel()

    async def _clean_tmp_dir_task(self):
        tmp_file_list = await aos.listdir(self._tmp_dir)
        if tmp_file_list:
            current_time = time.time()
            for temp_file in tmp_file_list:
                path = self._tmp_dir / temp_file
                if current_time - await aos.path.getatime(path) > self._CLEAN_AFTER_SEC:
                    await aos.remove(path)
