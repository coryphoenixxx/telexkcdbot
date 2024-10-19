import warnings
from dataclasses import dataclass
from typing import ClassVar

from PIL import Image, ImageSequence
from PIL.Image import Image as PILImage

from backend.application.image.exceptions import ImageConversionError
from backend.application.image.interfaces import ImageFileProcessorInterface
from backend.domain.value_objects.image_file import ImageFileObj, ImageFormat

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


@dataclass(slots=True)
class ImageFileProcessor(ImageFileProcessorInterface):
    MAX_IMAGE_PIXELS: ClassVar[int] = int(1024 * 1024 * 1024 // 4 // 3)
    MAX_WEBP_SIDE_SIZE: ClassVar[int] = 16383

    def convert_to_webp(self, original: ImageFileObj) -> ImageFileObj:
        with Image.open(original.source) as image:
            if self._has_too_large_side_sizes(image):
                raise ImageConversionError(original.source, "Image is too large.")

            if self._is_animation(image):
                raise ImageConversionError(original.source, "Image is an animation.")

            converted_abs_path = original.source.with_name(original.source.stem + "_converted")

            image.save(
                fp=converted_abs_path,
                format=ImageFormat.WEBP,
                lossless=original.format == ImageFormat.PNG,
                quality=85 if original.format != ImageFormat.PNG else 100,
                optimize=True,
            )

        converted = ImageFileObj(converted_abs_path)

        if converted.size > original.size:
            converted.source.unlink()
            raise ImageConversionError(
                path=original.source,
                reason="Converted image file size is larger than original image file size.",
            )

        return converted

    def _has_too_large_side_sizes(self, image: PILImage) -> bool:
        return any(
            [
                (image.height * image.width) > self.MAX_IMAGE_PIXELS,
                image.width > self.MAX_WEBP_SIDE_SIZE,
                image.height > self.MAX_WEBP_SIDE_SIZE,
            ]
        )

    def _is_animation(self, image: PILImage) -> bool:
        frames = 0
        for _ in ImageSequence.Iterator(image):
            if frames > 1:
                break
            frames += 1
        return frames > 1
