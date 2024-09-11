from dataclasses import dataclass

from backend.application.common.exceptions import BaseAppError


@dataclass(slots=True)
class TagNotFoundError(BaseAppError):
    tag_id: int

    @property
    def message(self) -> str:
        return f"A tag (id={self.tag_id}) not found."


@dataclass(slots=True)
class TagNameUniqueError(BaseAppError):
    name: str

    @property
    def message(self) -> str:
        return f"A tag name ({self.name}) already exists."
