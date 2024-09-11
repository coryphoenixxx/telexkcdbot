import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import pillow_avif  # type: ignore[import-untyped] # noqa: F401
from PIL import Image, ImageSequence
from PIL.Image import Image as ImageObj

from backend.application.comic.exceptions.translation_image import ImageConversionError
from backend.application.comic.interfaces.image_converter import ImageConverterInterface
from backend.application.common.dtos import ImageFormat

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


@dataclass(slots=True)
class ImageConverter(ImageConverterInterface):
    MAX_IMAGE_PIXELS: ClassVar[int] = int(1024 * 1024 * 1024 // 4 // 3)
    MAX_WEBP_SIDE_SIZE: ClassVar[int] = 16383

    def convert_to_webp(self, original: Path) -> Path:
        with Image.open(original) as image:
            if self._has_too_large_side_sizes(image):
                raise ImageConversionError(original, "The image is too large.")

            if self._is_animation(image):
                raise ImageConversionError(original, "The image is an animation.")

            converted_path = original.with_name(original.stem + "_converted").with_suffix(".webp")

            fmt = ImageFormat(original.suffix[1:])
            image.save(
                fp=converted_path,
                format="webp",
                lossless=fmt == ImageFormat.PNG,
                quality=85 if fmt != ImageFormat.PNG else 100,
                optimize=True,
            )

        if converted_path.stat().st_size > original.stat().st_size:
            converted_path.unlink()
            raise ImageConversionError(
                original,
                "The converted image file size is larger than the original image file size.",
            )

        return converted_path

    def _has_too_large_side_sizes(self, image: ImageObj) -> bool:
        return any(
            [
                (image.height * image.width) > self.MAX_IMAGE_PIXELS,
                image.width > self.MAX_WEBP_SIDE_SIZE,
                image.height > self.MAX_WEBP_SIDE_SIZE,
            ]
        )

    def _is_animation(self, image: ImageObj) -> bool:
        frames = 0
        for _ in ImageSequence.Iterator(image):
            if frames > 1:
                break
            frames += 1
        return frames > 1
