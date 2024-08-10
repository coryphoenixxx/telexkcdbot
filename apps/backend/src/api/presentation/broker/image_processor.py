import logging
import warnings
from pathlib import Path

from PIL import Image, ImageSequence
from shared.my_types import ImageFormat

warnings.simplefilter("ignore", Image.DecompressionBombWarning)

logger = logging.getLogger(__name__)


class ImageProcessor:
    MAX_WEBP_SIZE = 16383

    def process(self, original_abs_path: Path) -> tuple[Path, Path]:
        try:
            img_obj = Image.open(original_abs_path)
        except FileNotFoundError:
            logger.error(f"Image file not found: {original_abs_path}")
        else:
            try:
                converted_abs_path = None

                if not self.is_animation(img_obj):
                    converted_abs_path = self.convert_to_webp(img_obj, original_abs_path)

                thumbnail_abs_path = self.create_thumbnail(
                    img_obj,
                    converted_abs_path or original_abs_path,
                    (200, 200),
                )
            except Exception as err:
                logger.exception(err, extra={"path": original_abs_path})
            else:
                return converted_abs_path, thumbnail_abs_path

    def convert_to_webp(self, img_obj: Image, img_path: Path) -> Path | None:
        if any(
            [
                (img_obj.height * img_obj.width) > Image.MAX_IMAGE_PIXELS,
                img_obj.width > self.MAX_WEBP_SIZE,
                img_obj.height > self.MAX_WEBP_SIZE,
            ],
        ):
            return None

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

    def create_thumbnail(
        self,
        img_obj: Image,
        img_path: Path,
        sizes: tuple[int, int],
    ) -> Path:
        old_name_parts = img_path.stem.split("_")
        new_name = "_".join(old_name_parts[:-2]) + f"_{sizes[0]}x{sizes[1]}_thumb"

        thumbnail_abs_path = img_path.with_name(new_name + img_path.suffix)

        img_obj.thumbnail(sizes)
        img_obj.save(thumbnail_abs_path)

        return thumbnail_abs_path

    @staticmethod
    def is_animation(img_obj: Image) -> bool:
        frames = 0
        for _ in ImageSequence.Iterator(img_obj):
            if frames > 1:
                break
            frames += 1

        return frames > 1
