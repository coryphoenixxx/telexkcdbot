from functools import singledispatchmethod
from typing import Any, NoReturn, Protocol

from pydantic import BaseModel


class PostProcessImageMessage(BaseModel):
    image_id: int


class NewComicMessage(BaseModel):
    comic_id: int


class PublisherRouterInterface(Protocol):
    @singledispatchmethod
    async def publish(self, msg: Any, **kwargs: Any) -> NoReturn:
        raise NotImplementedError

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: PostProcessImageMessage, **kwargs: Any) -> None: ...

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: NewComicMessage, **kwargs: Any) -> None: ...
