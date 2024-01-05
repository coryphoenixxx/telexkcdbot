from fastapi import FastAPI

from src.app.comics.exceptions import ComicNotFoundError, comic_not_found_exc_handler
from src.app.comics.images.exceptions import (
    ImageBadMetadataError,
    UnsupportedImageFormatError,
    UploadExceedLimitError,
    UploadFileIsEmpty,
    image_bad_metadata_exc_handler,
    unsupported_image_format_exc_handler,
    upload_exceed_limit_exc_handler,
    upload_file_is_empty_exc_handler,
)
from src.app.comics.translations.exceptions import (
    TranslationImagesNotCreatedError,
    translation_images_not_found_exc_handler,
)


def register_exceptions(app: FastAPI):
    app.add_exception_handler(ComicNotFoundError, comic_not_found_exc_handler)
    app.add_exception_handler(ImageBadMetadataError, image_bad_metadata_exc_handler)
    app.add_exception_handler(UnsupportedImageFormatError, unsupported_image_format_exc_handler)
    app.add_exception_handler(UploadExceedLimitError, upload_exceed_limit_exc_handler)
    app.add_exception_handler(UploadFileIsEmpty, upload_file_is_empty_exc_handler)
    app.add_exception_handler(TranslationImagesNotCreatedError, translation_images_not_found_exc_handler)
