import asyncio
from pathlib import Path

import aiohttp
from aiohttp import ClientResponse
from src.repositories.comic_repository import ComicRepository
from src.repositories.image_repository import ImageRepository


class ConverterService:
    converter_url: str
    background_tasks: set

    @classmethod
    def setup(cls, converter_url: str):
        cls.converter_url = converter_url
        cls.background_tasks = set()

    def __init__(self, comic_repo: ComicRepository, image_repo: ImageRepository):
        self._comic_repo = comic_repo
        self._image_repo = image_repo

    async def create_conversion_task(self, comic_id, lang):
        task = asyncio.create_task(self.convert_to_webp(comic_id, lang))
        self.background_tasks.add(task)

    async def convert_to_webp(self, comic_id, lang):
        await asyncio.sleep(5)
        new_rel_path = await self.send_image()
        await self._comic_repo.update_translation_image(comic_id, lang, str(new_rel_path))
        await self._image_repo.delete()

    async def send_image(self):
        async with self._image_repo(mode='rb') as f, aiohttp.ClientSession() as session:
            resp: ClientResponse = await session.post(
                url=self.converter_url + '/convert',
                data={'image': await f.read()},
            )

            if resp.status == 200:  # if resp != 200
                # if compression ratio < 0
                new_image_repo = ImageRepository(self._image_repo.work_dir)
                new_image_name = Path(self._image_repo.filepath).with_suffix('.webp').name

                async with new_image_repo(name=new_image_name, mode='wb') as f2:
                    await f2.write(await resp.content.read())
        return new_image_repo.rel_path
