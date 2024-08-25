from dishka import FromDishka
from faststream.nats import JStream, NatsRouter

from backend.application.services import TranslationImageService
from backend.core.value_objects import TranslationImageID
from backend.infrastructure.broker.messages import ImageProcessInMessage

router = NatsRouter()


@router.subscriber(
    subject="internal.api.images.process.in",
    queue="process_images_in_queue",
    stream=JStream(
        name="process_images_in_stream",
        max_age=600,
    ),
    pull_sub=True,
    durable="image_processor",
)
async def process_image(
    msg: ImageProcessInMessage,
    *,
    service: FromDishka[TranslationImageService]
) -> None:
    await service.convert_and_update(TranslationImageID(msg.image_id))
