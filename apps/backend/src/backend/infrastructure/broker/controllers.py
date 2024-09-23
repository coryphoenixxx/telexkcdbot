from dishka import FromDishka
from faststream.nats import JStream, NatsRouter

from backend.application.comic.services import ProcessTranslationImageInteractor
from backend.application.common.interfaces import ProcessTranslationImageMessage

router = NatsRouter()


@router.subscriber(
    subject="images.convert",
    queue="convert_image_queue",
    stream=JStream(name="stream_name", max_age=60 * 60, declare=True),
    pull_sub=True,
    durable="durable_name",
)
async def process_image(
    msg: ProcessTranslationImageMessage,
    *,
    service: FromDishka[ProcessTranslationImageInteractor],
) -> None:
    await service.execute(
        temp_image_id=msg.temp_image_id,
        translation_image_id=msg.translation_image_id,
    )
