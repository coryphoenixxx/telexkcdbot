from pathlib import Path, PosixPath

import aiofiles.os


class ImageRepository:
    def __init__(self, work_dir: str | Path):
        self.work_dir = work_dir
        self._mode = None
        self._file_abs_path: PosixPath | None = None
        self._file_obj = None

    @property
    def filepath(self):
        return self._file_abs_path

    @property
    def rel_path(self):
        return str(self._file_abs_path).split('static')[1]

    def __call__(self, mode: str, name: str | None = None):
        self._file_abs_path = (Path(self.work_dir) / name).resolve() if name else self._file_abs_path
        self._mode = mode
        return self

    async def __aenter__(self):
        self._file_obj = await aiofiles.open(self._file_abs_path, mode=self._mode)
        return self._file_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and 'w' in self._mode:
            await self.delete()
        await self._file_obj.close()

    async def rename(self, new_name: str):
        new_abs_path: PosixPath = self._file_abs_path.with_name(new_name)
        await aiofiles.os.rename(self._file_abs_path, new_abs_path)
        self._file_abs_path = new_abs_path
        return new_abs_path

    async def delete(self):
        await aiofiles.os.remove(self._file_abs_path)
