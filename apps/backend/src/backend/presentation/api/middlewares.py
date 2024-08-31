import logging
from dataclasses import dataclass
from types import MappingProxyType

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.application.services.comic import (
    OriginalTranslationOperationForbiddenError,
    TranslationIsAlreadyPublishedError,
)
from backend.core.exceptions.base import BaseAppError
from backend.infrastructure.database.repositories.comic import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from backend.infrastructure.database.repositories.tag import TagNameUniqueError, TagNotFoundError
from backend.infrastructure.database.repositories.translation import (
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from backend.infrastructure.filesystem.translation_image_file_manager import TempImageNotFoundError
from backend.infrastructure.upload_image_manager import (
    UnsupportedImageFormatError,
    UploadedImageReadError,
    UploadImageIsEmptyError,
    UploadImageSizeExceededLimitError,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True, eq=False)
class AppErrorIsNotRegisteredError(Exception):
    err_name: str

    @property
    def message(self) -> str:
        return f"Error recognized ({self.err_name}) but not registered."


ERROR_TO_STATUS_MAP = MappingProxyType(
    {
        id(UploadImageIsEmptyError): status.HTTP_400_BAD_REQUEST,
        id(UploadedImageReadError): status.HTTP_400_BAD_REQUEST,
        id(UploadImageSizeExceededLimitError): status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        id(UnsupportedImageFormatError): status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        id(ComicNotFoundError): status.HTTP_404_NOT_FOUND,
        id(ComicNumberAlreadyExistsError): status.HTTP_409_CONFLICT,
        id(ExtraComicTitleAlreadyExistsError): status.HTTP_404_NOT_FOUND,
        id(TempImageNotFoundError): status.HTTP_400_BAD_REQUEST,
        id(OriginalTranslationOperationForbiddenError): status.HTTP_400_BAD_REQUEST,
        id(TranslationAlreadyExistsError): status.HTTP_409_CONFLICT,
        id(TranslationNotFoundError): status.HTTP_404_NOT_FOUND,
        id(TagNotFoundError): status.HTTP_404_NOT_FOUND,
        id(TagNameUniqueError): status.HTTP_409_CONFLICT,
        id(TranslationIsAlreadyPublishedError): status.HTTP_409_CONFLICT,
    },
)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            try:
                return await call_next(request)
            except BaseAppError as err:
                err_class = ERROR_TO_STATUS_MAP.get(id(err.__class__))

                if err_class is None:
                    raise AppErrorIsNotRegisteredError(err.__class__.__name__) from None

                return ORJSONResponse(
                    status_code=err_class,
                    content={"error": err.message},
                )
        except Exception as err:
            match err:
                case AppErrorIsNotRegisteredError():
                    logger.exception(err.message)
                case _:
                    logger.exception("Something went wrong.")
            return ORJSONResponse(
                status_code=500,
                content={
                    "error": "An unexpected error occurred.",
                },
            )


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
