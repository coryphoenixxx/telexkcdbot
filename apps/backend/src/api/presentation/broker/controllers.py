from dishka import FromDishka as Depends
from faststream import Logger
from faststream.nats import JStream, NatsRouter
from PIL import Image
from shared.messages import ImageProcessInMessage

from api.application.services import TranslationImageService
from api.presentation.broker.image_processor import convert_to_webp, create_thumbnail, is_animation

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
    logger: Logger,
    service: Depends[TranslationImageService],
) -> None:
    original_abs_path = msg.original_abs_path

    try:
        img_obj = Image.open(original_abs_path)
    except FileNotFoundError:
        logger.error(f"Image file not found: {original_abs_path}")
    else:
        try:
            converted_abs_path = None

            if not is_animation(img_obj):
                converted_abs_path = convert_to_webp(img_obj, original_abs_path)

            thumbnail_abs_path = create_thumbnail(img_obj, converted_abs_path or original_abs_path)
        except Exception as err:
            logger.exception(err, extra={"path": original_abs_path})
        else:
            await service.update(
                image_id=msg.image_id,
                converted_abs_path=converted_abs_path,
                thumbnail_abs_path=thumbnail_abs_path,
            )
