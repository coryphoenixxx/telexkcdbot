from collections.abc import Generator
from pathlib import Path

import pytest
from filetype import filetype
from PIL import Image

from backend.domain.value_objects import ImageFileObj
from backend.domain.value_objects.image_file import ImageFormat
from backend.infrastructure.image_processor import ImageFileProcessor


@pytest.fixture(scope="session")
def converter() -> ImageFileProcessor:
    return ImageFileProcessor()


@pytest.fixture(scope="session")
def test_images_dir() -> Path:
    return Path(__file__).resolve().parent / "test_images"


@pytest.fixture(scope="function")
def clean_up(test_images_dir: Path) -> Generator[None, None, None]:
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
    converter: ImageFileProcessor,
    test_images_dir: Path,
    image_filename: str,
    clean_up: None,  # noqa: ARG001
) -> None:
    original = ImageFileObj(test_images_dir / image_filename)
    converted = converter.convert_to_webp(original)

    assert str(converted.source).endswith("_converted")
    assert original.source.parent == original.source.parent
    assert filetype.guess_extension(converted.source) == ImageFormat.WEBP
    assert converted.size < original.size

    with (
        Image.open(original.source) as original_image,
        Image.open(converted.source) as converted_image,
    ):
        assert original_image.size == converted_image.size
