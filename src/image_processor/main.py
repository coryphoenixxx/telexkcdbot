import logging

from faststream import FastStream
from faststream.nats import JStream, NatsBroker
from PIL import Image
from shared.types import ImageProcessInMessage, ImageProcessOutMessage

from image_processor.utils import convert_to_webp, create_thumbnail

broker = NatsBroker()
app = FastStream(broker)

stream = JStream(name="stream", declare=False)


@broker.subscriber(
    subject="image_processing",
    queue="image_processing_queue",
    stream=stream,
)
async def process_image_handler(msg: ImageProcessInMessage):
    original_abs_path = msg.original_abs_path

    try:
        img_obj = Image.open(original_abs_path)
    except FileNotFoundError:
        logging.error("image file not found!")
    else:
        converted_abs_path = convert_to_webp(img_obj, original_abs_path)
        thumbnail_abs_path = create_thumbnail(img_obj, converted_abs_path or original_abs_path)

        await broker.publish(
            message=ImageProcessOutMessage(
                image_id=msg.image_id,
                converted_abs_path=converted_abs_path,
                thumbnail_abs_path=thumbnail_abs_path,
            ),
            subject="processed_images",
            stream="stream",
        )
