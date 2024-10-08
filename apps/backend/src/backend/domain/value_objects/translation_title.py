from dataclasses import dataclass

from backend.domain.exceptions import BaseAppError
from backend.domain.utils import slugify

MIN_TITLE_LENGTH = 1
MAX_TITLE_LENGTH = 100


@dataclass(slots=True)
class TranslationTitleLengthError(BaseAppError):
    title: str

    @property
    def message(self) -> str:
        return (
            f"Translation title length must be between "
            f"{MIN_TITLE_LENGTH} and {MAX_TITLE_LENGTH} characters."
        )


@dataclass(slots=True, frozen=True)
class TranslationTitle:
    value: str

    def __post_init__(self) -> None:
        if not (MIN_TITLE_LENGTH <= len(self.value) <= MAX_TITLE_LENGTH):
            raise TranslationTitleLengthError(self.value)

    @property
    def slug(self) -> str:
        return slugify(self.value)
