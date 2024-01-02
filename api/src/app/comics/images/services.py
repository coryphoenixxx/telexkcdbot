from .dtos import TranslationImageDTO
from .repo import TranslationImageRepo
from .utils import ImageFileSaveHelper


class TranslationImageService:
    def __init__(self, repo: TranslationImageRepo, file_saver: ImageFileSaveHelper):
        self._repo = repo
        self._file_saver = file_saver

    async def create(self, image_dto: TranslationImageDTO) -> int:
        image_save_path = await self._file_saver.save(image_dto)
        image_id = await self._repo.create(image_dto, image_save_path)
        return image_id
