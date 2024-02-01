import warnings
from pathlib import Path

from PIL import Image
from shared.types import ImageFormat

THUMB_SIZE = (200, 200)

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


def convert_to_webp(img_obj: Image, img_path: Path) -> Path | None:
    fmt = ImageFormat(img_path.suffix[1:])

    if fmt == ImageFormat.GIF or (img_obj.height * img_obj.width) > Image.MAX_IMAGE_PIXELS:
        return None

    converted_abs_path = img_path.with_name(
        img_path.stem.replace("_original", "_converted"),
    ).with_suffix(".webp")

    img_obj.save(
        fp=converted_abs_path,
        format="webp",
        lossless=fmt == ImageFormat.PNG,
        quality=85 if fmt != ImageFormat.PNG else 100,
        optimize=True,
    )

    return converted_abs_path


def create_thumbnail(img_obj: Image, img_path: Path) -> Path:
    old_name_parts = img_path.stem.split("_")
    new_name = "_".join(old_name_parts[:-2]) + f"_{THUMB_SIZE[0]}x{THUMB_SIZE[1]}" + "_thumb"

    thumbnail_abs_path = img_path.with_name(new_name + img_path.suffix)

    img_obj.thumbnail(THUMB_SIZE)
    img_obj.save(thumbnail_abs_path)

    return thumbnail_abs_path
