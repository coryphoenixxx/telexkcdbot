from functools import singledispatchmethod

from faststream.nats import NatsBroker

from backend.infrastructure.broker.messages import ConvertImageMessage, NewComicMessage


class PublisherContainer:
    def __init__(self, broker: NatsBroker):
        self._broker = broker
        self._converter_publisher = broker.publisher(subject="images.convert", stream="stream_name")
        self._new_comic_publisher = broker.publisher(subject="comics.new", stream="stream_name")

    @singledispatchmethod
    async def publish(self, msg):
        raise NotImplementedError

    @publish.register
    async def _(self, msg: ConvertImageMessage) -> None:
        await self._converter_publisher.publish(msg)

    @publish.register
    async def _(self, msg: NewComicMessage) -> None:
        await self._new_comic_publisher.publish(msg)
