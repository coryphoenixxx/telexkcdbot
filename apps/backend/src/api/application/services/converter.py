from faststream.nats import NatsBroker
from shared.messages import ImageProcessInMessage

from api.core.value_objects import TranslationImageID


class Converter:
    def __init__(self, broker: NatsBroker) -> None:
        self._broker = broker

    async def convert(self, image_id: TranslationImageID):
        await self._broker.publish(
            message=ImageProcessInMessage(image_id=image_id),
            subject="internal.api.images.process.in",
            stream="process_images_in_stream",
        )
