from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Any, NoReturn

from faststream.nats.publisher.asyncapi import AsyncAPIPublisher

from backend.application.common.interfaces import (
    ConvertImageMessage,
    NewComicMessage,
    PublisherRouterInterface,
)


@dataclass(slots=True)
class PublisherRouter(PublisherRouterInterface):
    converter_publisher: AsyncAPIPublisher
    new_comic_publisher: AsyncAPIPublisher

    @singledispatchmethod
    async def publish(self, msg: Any, **kwargs: Any) -> NoReturn:
        raise NotImplementedError

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: ConvertImageMessage, **kwargs: Any) -> None:
        await self.converter_publisher.publish(msg, **kwargs)

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: NewComicMessage, **kwargs: Any) -> None:
        await self.new_comic_publisher.publish(msg, **kwargs)
