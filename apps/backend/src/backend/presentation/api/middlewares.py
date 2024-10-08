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
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
    TagNameAlreadyExistsError,
    TagNotFoundError,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from backend.application.common.exceptions import TempFileNotFoundError
from backend.application.image.exceptions import (
    ImageAlreadyHasOwnerError,
    ImageIsEmptyError,
    ImageNotFoundError,
    ImageSizeExceededLimitError,
)
from backend.domain.entities.translation import OriginalTranslationOperationForbiddenError
from backend.domain.exceptions import BaseAppError
from backend.domain.value_objects.image_file import ImageReadError, UnsupportedImageFormatError
from backend.domain.value_objects.tag_name import TagNameLengthError
from backend.domain.value_objects.translation_title import TranslationTitleLengthError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AppErrorIsNotRegisteredError(Exception):
    err_name: str

    @property
    def message(self) -> str:
        return f"Error recognized ({self.err_name}) but not registered."


ERROR_TO_STATUS_MAP = MappingProxyType(
    {
        ImageIsEmptyError: status.HTTP_400_BAD_REQUEST,
        ImageReadError: status.HTTP_400_BAD_REQUEST,
        ImageSizeExceededLimitError: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        UnsupportedImageFormatError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ComicNotFoundError: status.HTTP_404_NOT_FOUND,
        ComicNumberAlreadyExistsError: status.HTTP_409_CONFLICT,
        ExtraComicTitleAlreadyExistsError: status.HTTP_409_CONFLICT,
        TempFileNotFoundError: status.HTTP_404_NOT_FOUND,
        ImageNotFoundError: status.HTTP_404_NOT_FOUND,
        ImageAlreadyHasOwnerError: status.HTTP_409_CONFLICT,
        OriginalTranslationOperationForbiddenError: status.HTTP_400_BAD_REQUEST,
        TranslationAlreadyExistsError: status.HTTP_409_CONFLICT,
        TranslationNotFoundError: status.HTTP_404_NOT_FOUND,
        TranslationTitleLengthError: status.HTTP_400_BAD_REQUEST,
        TagNameLengthError: status.HTTP_400_BAD_REQUEST,
        TagNotFoundError: status.HTTP_404_NOT_FOUND,
        TagNameAlreadyExistsError: status.HTTP_409_CONFLICT,
    },
)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            try:
                return await call_next(request)
            except BaseAppError as err:
                err_status = ERROR_TO_STATUS_MAP.get(err.__class__)

                if err_status is None:
                    raise AppErrorIsNotRegisteredError(err.__class__.__name__) from None

                return ORJSONResponse(
                    status_code=err_status,
                    content={"error": err.message},
                )
        except AppErrorIsNotRegisteredError as err:
            logger.exception(err.message)
            return ORJSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "An unexpected error occurred.",
                },
            )
        except Exception:
            logger.exception("Unexpected error occurred")
            return ORJSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
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
