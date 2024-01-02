import asyncio
import time
from pathlib import Path

import aiofiles.os as aos

_CLEANER_SLEEP_SEC = 60 * 5
_CLEAN_AFTER_SEC = 60


async def cleaner():
    temp_dir = Path('./.tmp')
    while True:
        temp_file_list = await aos.listdir(temp_dir)
        if temp_file_list:
            current_time = time.time()
            for temp_file in temp_file_list:
                path = temp_dir / temp_file
                if current_time - await aos.path.getatime(path) > _CLEAN_AFTER_SEC:
                    await aos.remove(path)
        await asyncio.sleep(_CLEANER_SLEEP_SEC)
