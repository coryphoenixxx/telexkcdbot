from typing import Any


class BaseAppError(Exception):

    @property
    def detail(self) -> str | dict[str, Any]:
        raise NotImplementedError
