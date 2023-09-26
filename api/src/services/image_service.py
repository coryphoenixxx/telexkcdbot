import magic
from aiohttp import BodyPartReader
from src.helpers.exceptions import BigSizeError, InvalidImageExtensionError
from src.repositories.image_repository import ImageRepository


class ImageReaderService:
    supported_extensions: tuple
    image_max_size: int
    comic_images_dir: str

    @classmethod
    def setup(cls, config):
        cls.supported_extensions = tuple(config.img.supported_extensions.split(','))
        cls.image_max_size = config.img.image_max_size
        cls.comic_images_dir = config.img.images_dir

    def __init__(self):
        self._repo = ImageRepository(work_dir=self.comic_images_dir)

    async def read_image_from_body_part(self, stem: str, image_body_part: BodyPartReader):
        async with self._repo(name=stem, mode='wb') as f:
            size = 0
            while True:
                chunk = await image_body_part.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > self.image_max_size:
                    raise BigSizeError("So big image size!")
                await f.write(chunk)

            extension = magic.from_file(filename=f.name, mime=True).split('/')[1]
            if extension not in self.supported_extensions:
                raise InvalidImageExtensionError("Invalid image extension!")

            await self._repo.rename(f"{stem}.{extension}")
        return self._repo
