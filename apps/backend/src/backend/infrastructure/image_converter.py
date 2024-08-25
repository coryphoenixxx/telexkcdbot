import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence
from PIL.Image import Image as ImageObj

from backend.infrastructure.filesystem.dtos import ImageFormat

warnings.simplefilter("ignore", Image.DecompressionBombWarning)


@dataclass(frozen=True, eq=False, slots=True)
class ImageConversionError(Exception):
    reason: str

    @property
    def message(self) -> str:
        return f"The image was not converted. Reason: `{self.reason}`"


class ImageConverter:
    MAX_WEBP_SIDE_SIZE = 16383

    def convert_to_webp(self, path: Path) -> Path:
        path = Path(path)
        fmt = ImageFormat(path.suffix[1:])

        if fmt == ImageFormat.WEBP:
            raise ImageConversionError("It looks like the image is already converted.")

        with Image.open(path) as image:
            image.load()

            if self._has_invalid_side_sizes(image):
                raise ImageConversionError("The image is too large.")

            if self._is_animation(image):
                raise ImageConversionError("The image is an animation.")

            new_path = path.with_name(path.stem + "_converted").with_suffix(".webp")

            image.save(
                fp=new_path,
                format="webp",
                lossless=fmt == ImageFormat.PNG,
                quality=85 if fmt != ImageFormat.PNG else 100,
                optimize=True,
            )

            return new_path

    def _has_invalid_side_sizes(self, image: ImageObj) -> bool:
        return any(
            [
                (image.height * image.width) > Image.MAX_IMAGE_PIXELS,
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
