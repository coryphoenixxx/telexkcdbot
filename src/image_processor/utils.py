import warnings
from pathlib import Path

from faststream import Logger
from PIL import Image
from shared.types import ImageFormat

THUMB_SIZE = (200, 200)
MAX_WEBP_SIZE = 16383

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


def convert_to_webp(img_obj: Image, img_path: Path, logger: Logger) -> Path | None:
    fmt = ImageFormat(img_path.suffix[1:])

    if any(
        [
            fmt == ImageFormat.GIF,
            (img_obj.height * img_obj.width) > Image.MAX_IMAGE_PIXELS,
            img_obj.width > MAX_WEBP_SIZE,
            img_obj.height > MAX_WEBP_SIZE,
        ],
    ):
        return

    converted_abs_path = img_path.with_name(
        img_path.stem.replace("_original", "_converted"),
    ).with_suffix(".webp")

    try:
        img_obj.save(
            fp=converted_abs_path,
            format="webp",
            lossless=fmt == ImageFormat.PNG,
            quality=85 if fmt != ImageFormat.PNG else 100,
            optimize=True,
        )
    except Exception as err:
        logger.error(err)
        logger.error(img_path)
    else:
        return converted_abs_path


def create_thumbnail(img_obj: Image, img_path: Path, logger: Logger) -> Path | None:
    old_name_parts = img_path.stem.split("_")
    new_name = "_".join(old_name_parts[:-2]) + f"_{THUMB_SIZE[0]}x{THUMB_SIZE[1]}" + "_thumb"

    thumbnail_abs_path = img_path.with_name(new_name + img_path.suffix)

    try:
        img_obj.thumbnail(THUMB_SIZE)
        img_obj.save(thumbnail_abs_path)
    except Exception as err:
        logger.error(err)
        logger.error(img_path)
    else:
        return thumbnail_abs_path
