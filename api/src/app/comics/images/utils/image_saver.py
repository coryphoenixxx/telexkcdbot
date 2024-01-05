from pathlib import Path
from uuid import uuid4

import aiofiles.os as aos
from slugify import slugify

from src.app.comics.images.dtos import TranslationImageDTO


class ImageFileSaver:
    _IMAGES_URL_PREFIX = 'images/comics/'

    def __init__(self, static_dir: str):
        self._static_dir = Path(static_dir).absolute()

    async def save(self, img: TranslationImageDTO) -> str:
        rel_path = self._IMAGES_URL_PREFIX + self._build_rel_path(img)

        new_path = self._static_dir / rel_path

        await aos.makedirs(new_path.parent, exist_ok=True)
        await aos.replace(img.image_obj.path, new_path)

        return rel_path

    @staticmethod
    def _build_rel_path(img_dto: TranslationImageDTO) -> str:
        if img_dto.issue_number and not img_dto.is_draft:
            return (f"{img_dto.issue_number}/{img_dto.language}/"
                    f"{img_dto.version}.{img_dto.image_obj.format_}")

        if img_dto.issue_number and img_dto.is_draft:
            return (f"{img_dto.issue_number}/{img_dto.language}"
                    f"/drafts/{uuid4()}.{img_dto.image_obj.format_}")

        if img_dto.en_title and not img_dto.is_draft:
            return (f"extras/{slugify(img_dto.en_title, separator='_')}/"
                    f"{img_dto.language}/{img_dto.version}.{img_dto.image_obj.format_}")

        if img_dto.en_title and img_dto.is_draft:
            return (f"extras/{slugify(img_dto.en_title, separator='_')}/{img_dto.language}"
                    f"/drafts/{uuid4()}.{img_dto.image_obj.format_}")
