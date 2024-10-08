from dishka import FromDishka
from faststream.nats import JStream, NatsRouter

from backend.application.common.interfaces import PostProcessImageMessage
from backend.application.image.services import ProcessImageInteractor
from backend.domain.value_objects import ImageId

router = NatsRouter()


@router.subscriber(
    subject="images.convert",
    queue="convert_image_queue",
    stream=JStream(name="stream_name", max_age=60 * 60, declare=True),
    pull_sub=True,
    durable="durable_name",
)
async def process_image(
    msg: PostProcessImageMessage,
    *,
    interactor: FromDishka[ProcessImageInteractor],
) -> None:
    await interactor.execute(image_id=ImageId(msg.image_id))
