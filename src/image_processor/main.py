import logging

from PIL import Image
from faststream import FastStream
from faststream.nats import NatsBroker

from image_processor.utils import convert_to_webp, create_thumbnail
from shared.messages import ImageProcessInMessage, ImageProcessOutMessage

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber(
    subject="internal.api.images.process.in",
    queue="process_images_in_queue",
    stream="process_images_in_stream",
)
async def process_image_handler(msg: ImageProcessInMessage):
    original_abs_path = msg.original_abs_path

    try:
        img_obj = Image.open(original_abs_path)
    except FileNotFoundError:
        logging.error("Image file not found!")
    else:
        converted_abs_path = convert_to_webp(img_obj, original_abs_path)
        thumbnail_abs_path = create_thumbnail(img_obj, converted_abs_path or original_abs_path)

        await broker.publish(
            message=ImageProcessOutMessage(
                image_id=msg.image_id,
                converted_abs_path=converted_abs_path,
                thumbnail_abs_path=thumbnail_abs_path,
            ),
            subject="internal.api.images.process.out",
            stream="process_images_out_stream",
        )
