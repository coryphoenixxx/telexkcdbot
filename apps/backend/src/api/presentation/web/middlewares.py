import logging
from types import MappingProxyType

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.application.exceptions.base import (
    BaseAppError,
    BaseBadRequestError,
    BaseConflictError,
    BaseNotFoundError,
)
from api.application.exceptions.image import (
    UnsupportedImageFormatError,
    UploadExceedSizeLimitError,
)
from api.application.exceptions.user import InvalidCredentialsError

logger = logging.getLogger(__name__)

ERROR_TO_STATUS_MAP = MappingProxyType(
    {
        BaseBadRequestError: status.HTTP_400_BAD_REQUEST,
        InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
        BaseNotFoundError: status.HTTP_404_NOT_FOUND,
        BaseConflictError: status.HTTP_409_CONFLICT,
        UploadExceedSizeLimitError: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        UnsupportedImageFormatError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    },
)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except BaseAppError as err:
            err_class = ERROR_TO_STATUS_MAP.get(err.__class__.__base__)
            if not err_class:
                err_class = ERROR_TO_STATUS_MAP[err.__class__]

            return ORJSONResponse(
                status_code=err_class,
                content=err.detail,
            )
        except Exception as err:
            logger.error(err, exc_info=True)
            return ORJSONResponse(
                status_code=500,
                content={
                    "message": "An unexpected error occurred.",
                },
            )


def register_middlewares(app: FastAPI):
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
