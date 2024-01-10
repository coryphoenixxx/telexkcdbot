from typing import Any


class BaseAppError(Exception):
    @property
    def status_code(self) -> int:
        raise NotImplementedError

    @property
    def detail(self) -> str | dict[str, Any]:
        raise NotImplementedError
