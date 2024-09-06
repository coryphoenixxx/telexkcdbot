from pathlib import Path

import pytest
from filetype import filetype
from PIL import Image

from backend.infrastructure.image_converter import ImageConverter


@pytest.fixture(scope="session")
def converter() -> ImageConverter:
    return ImageConverter()


@pytest.fixture(scope="session")
def test_images_dir() -> Path:
    return Path(__file__).resolve().parent / "test_images"


@pytest.mark.parametrize("image_filename", ["dummy.jpeg", "dummy.png", "dummy.webp"])
def test_convert_image_to_webp_success(
    converter: ImageConverter,
    test_images_dir: Path,
    image_filename: str,
) -> None:
    converted_path = None
    original = test_images_dir / image_filename
    try:
        converted_path = converter.convert_to_webp(original)

        assert str(converted_path).endswith("_converted.webp")
        assert original.parent == converted_path.parent
        assert filetype.guess_extension(converted_path) == "webp"
        assert converted_path.stat().st_size < original.stat().st_size

        with Image.open(original) as input_image, Image.open(converted_path) as converted_image:
            assert input_image.size == converted_image.size
    finally:
        if converted_path:
            converted_path.unlink()
