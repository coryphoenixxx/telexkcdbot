from dataclasses import dataclass

from api.core.exceptions.base import BaseNotFoundError


@dataclass
class TagNotFoundError(BaseNotFoundError):
    message: str = "A tag not found."


@dataclass
class TagNameUniqueError(BaseNotFoundError):
    message: str = "A tag name already exists."
