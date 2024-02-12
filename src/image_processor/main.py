
from faststream import FastStream, Logger
from faststream.nats import NatsBroker
from PIL import Image
from shared.messages import ImageProcessInMessage, ImageProcessOutMessage

from image_processor.utils import convert_to_webp, create_thumbnail

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber(
    subject="internal.api.images.process.in",
    queue="process_images_in_queue",
    stream="process_images_in_stream",
)
async def process_image_handler(msg: ImageProcessInMessage, logger: Logger):
    original_abs_path = msg.original_abs_path

    try:
        img_obj = Image.open(original_abs_path)
    except FileNotFoundError:
        logger.error("Image file not found!")
    else:
        converted_abs_path = convert_to_webp(img_obj, original_abs_path, logger)
        thumbnail_abs_path = create_thumbnail(
            img_obj, converted_abs_path or original_abs_path, logger,
        )

        await broker.publish(
            message=ImageProcessOutMessage(
                image_id=msg.image_id,
                converted_abs_path=converted_abs_path,
                thumbnail_abs_path=thumbnail_abs_path,
            ),
            subject="internal.api.images.process.out",
            stream="process_images_out_stream",
        )
