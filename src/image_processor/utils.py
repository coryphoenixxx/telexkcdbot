import warnings
from pathlib import Path

from PIL import Image, ImageSequence
from shared.types import ImageFormat

THUMB_SIZE = (200, 200)
MAX_WEBP_SIZE = 16383

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


def is_animation(img_obj: Image) -> bool:
    frames = 0
    for _ in ImageSequence.Iterator(img_obj):
        if frames > 1:
            break
        frames += 1

    return frames > 1


def convert_to_webp(img_obj: Image, img_path: Path) -> Path | None:
    if any(
        [
            (img_obj.height * img_obj.width) > Image.MAX_IMAGE_PIXELS,
            img_obj.width > MAX_WEBP_SIZE,
            img_obj.height > MAX_WEBP_SIZE,
        ],
    ):
        return

    converted_abs_path = img_path.with_name(
        img_path.stem.replace("_original", "_converted"),
    ).with_suffix(".webp")

    fmt = ImageFormat(img_path.suffix[1:])

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
    new_name = "_".join(old_name_parts[:-2]) + f"_{THUMB_SIZE[0]}x{THUMB_SIZE[1]}_thumb"

    thumbnail_abs_path = img_path.with_name(new_name + img_path.suffix)

    img_obj.thumbnail(THUMB_SIZE)
    img_obj.save(thumbnail_abs_path)

    return thumbnail_abs_path
