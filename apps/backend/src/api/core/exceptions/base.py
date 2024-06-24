from typing import Any


class BaseAppError(Exception):
    message: str

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


class BaseNotFoundError(BaseAppError): ...


class BaseConflictError(BaseAppError): ...


class BaseBadRequestError(BaseAppError): ...
