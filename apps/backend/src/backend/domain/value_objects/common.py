from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class PositiveInt:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("Must be positive integer.")


class NonNegativeInt(PositiveInt):
    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Must be greater than 0.")


class ComicId(PositiveInt): ...


class IssueNumber(PositiveInt): ...


class TagId(PositiveInt): ...


class TranslationId(PositiveInt): ...


class ImageId(PositiveInt): ...


@dataclass(slots=True, frozen=True)
class TempFileUUID:
    value: UUID
