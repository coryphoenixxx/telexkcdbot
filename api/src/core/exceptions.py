from typing import Any


class BaseAppException(Exception):

    @property
    def detail(self) -> str | dict[str, Any]:
        raise NotImplementedError
