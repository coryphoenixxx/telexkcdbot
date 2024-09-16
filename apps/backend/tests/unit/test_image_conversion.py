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


@pytest.fixture(scope="function")
def clean_up(test_images_dir: Path) -> None:
    files_before = set(test_images_dir.iterdir())
    yield
    files_after = set(test_images_dir.iterdir())
    for f in files_after - files_before:
        f.unlink()


@pytest.mark.parametrize(
    "image_filename",
    [
        "dummy.jpeg",
        "dummy.png",
        "dummy.webp",
    ],
)
def test_convert_image_to_webp_success(
    converter: ImageConverter,
    test_images_dir: Path,
    image_filename: str,
    clean_up: None,  # noqa: ARG001
) -> None:
    original, converted = test_images_dir / image_filename, None
    converted = converter.convert_to_webp(original)

    assert str(converted).endswith("_converted.webp")
    assert original.parent == converted.parent
    assert filetype.guess_extension(converted) == "webp"
    assert converted.stat().st_size < original.stat().st_size

    with Image.open(original) as input_image, Image.open(converted) as converted_image:
        assert input_image.size == converted_image.size
