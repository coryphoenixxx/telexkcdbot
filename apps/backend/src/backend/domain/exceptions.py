from dataclasses import dataclass


@dataclass
class BaseAppError(Exception):
    @property
    def message(self) -> str:
        return "A base application error occurred."
