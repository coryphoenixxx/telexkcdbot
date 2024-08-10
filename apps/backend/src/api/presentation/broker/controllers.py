from dishka import FromDishka as Depends
from faststream.nats import JStream, NatsRouter
from api.infrastructure.filesystem.image_file_manager import ImageFileManager
from shared.messages import ImageProcessInMessage

from api.application.services import TranslationImageService
from api.presentation.broker.image_processor import ImageProcessor

router = NatsRouter()


@router.subscriber(
    subject="internal.api.images.process.in",
    queue="process_images_in_queue",
    stream=JStream(
        name="process_images_in_stream",
        max_age=600,  # TODO: опираться на размер очереди
    ),
    pull_sub=True,
    durable="image_processor",
)
async def process_image(
    msg: ImageProcessInMessage,
    *,
    service: Depends[TranslationImageService],
    image_processor: Depends[ImageProcessor],
    file_manager: Depends[ImageFileManager],
) -> None:
    image_dto = await service.get_by_id(msg.image_id)
    image_abs_path = file_manager.rel_to_abs(image_dto.original_rel_path)
    converted, thumbnail = image_processor.process(original_abs_path=image_abs_path)

    await service.update(
        image_id=msg.image_id,
        converted_abs_path=converted,
        thumbnail_abs_path=thumbnail,
    )
