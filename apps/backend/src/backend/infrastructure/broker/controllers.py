from dishka import FromDishka
from faststream.nats import JStream, NatsRouter

from backend.application.comic.services import ConvertAndUpdateTranslationImageInteractor
from backend.application.common.interfaces import ConvertImageMessage
from backend.core.value_objects import TranslationImageID

router = NatsRouter()


@router.subscriber(
    subject="images.convert",
    queue="convert_image_queue",
    stream=JStream(name="stream_name", max_age=60 * 60, declare=True),
    pull_sub=True,
    durable="durable_name",
)
async def process_image(
    msg: ConvertImageMessage,
    *,
    service: FromDishka[ConvertAndUpdateTranslationImageInteractor],
) -> None:
    await service.execute(TranslationImageID(msg.image_id))
