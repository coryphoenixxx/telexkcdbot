from dataclasses import dataclass

from backend.domain.exceptions import BaseAppError


@dataclass(slots=True)
class UsernameAlreadyExistsError(BaseAppError):
    username: str

    @property
    def message(self) -> str:
        return f"User with this username ({self.username}) already exists."


@dataclass(slots=True)
class InvalidCredentialsError(BaseAppError):
    @property
    def message(self) -> str:
        return "Invalid credentials."
