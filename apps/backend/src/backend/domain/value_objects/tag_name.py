from dataclasses import dataclass

from backend.domain.exceptions import BaseAppError
from backend.domain.utils import slugify

TAG_NAME_MIN_LENGTH = 2
TAG_NAME_MAX_LENGTH = 50


@dataclass(slots=True)
class TagNameLengthError(BaseAppError):
    name: str

    @property
    def message(self) -> str:
        return (
            f"Tag name length must be between "
            f"{TAG_NAME_MIN_LENGTH} and {TAG_NAME_MAX_LENGTH} characters."
        )


@dataclass(slots=True, frozen=True)
class TagName:
    value: str

    def __post_init__(self) -> None:
        if not (TAG_NAME_MIN_LENGTH <= len(self.value) <= TAG_NAME_MAX_LENGTH):
            raise TagNameLengthError(self.value)

    @property
    def slug(self) -> str:
        return slugify(self.value)
