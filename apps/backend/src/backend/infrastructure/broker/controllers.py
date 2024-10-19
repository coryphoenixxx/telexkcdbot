from dishka import FromDishka
from faststream.nats import NatsRouter

from backend.application.common.interfaces import (
    ConvertImageMessage,
)
from backend.application.image.services import (
    ConvertImageInteractor,
)
from backend.domain.value_objects import ImageId
from backend.infrastructure.broker.stream import stream

router = NatsRouter()


@router.subscriber(
    subject="images.convert",
    queue="convert_image_queue",
    stream=stream,
    pull_sub=True,
    durable="durable_name",
)
async def process_image(
    msg: ConvertImageMessage,
    *,
    interactor: FromDishka[ConvertImageInteractor],
) -> None:
    await interactor.execute(image_id=ImageId(msg.image_id))
