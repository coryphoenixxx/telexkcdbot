from dataclasses import dataclass
from typing import Any

from api.application.exceptions.base import BaseAppError, BaseConflictError


@dataclass
class UsernameAlreadyExistsError(BaseConflictError):
    username: str
    message: str = "User with this username already exists."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "username": self.username,
        }


@dataclass
class InvalidCredentialsError(BaseAppError):
    message: str = "Invalid credentials."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}
