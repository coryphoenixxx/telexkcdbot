from dataclasses import dataclass
from functools import singledispatchmethod

from faststream.nats.publisher.asyncapi import AsyncAPIPublisher

from backend.infrastructure.broker.messages import ConvertImageMessage, NewComicMessage


@dataclass(slots=True, eq=False)
class PublisherContainer:
    converter_publisher: AsyncAPIPublisher
    new_comic_publisher: AsyncAPIPublisher

    @singledispatchmethod
    async def publish(self, msg, **kwargs):
        raise NotImplementedError

    @publish.register
    async def _(self, msg: ConvertImageMessage, **kwargs) -> None:
        await self.converter_publisher.publish(msg, **kwargs)

    @publish.register
    async def _(self, msg: NewComicMessage, **kwargs) -> None:
        await self.new_comic_publisher.publish(msg, **kwargs)
