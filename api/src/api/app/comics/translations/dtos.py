from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from api.app.comics.image_utils.types import ComicImageType
from api.core.types import LanguageCode


@dataclass(slots=True)
class ComicTranslationCreateDTO:
    comic_id: int
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    language_code: LanguageCode
    images: dict[ComicImageType, Path] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
