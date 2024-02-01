import logging

from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from api.core.exceptions import BaseAppError

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except BaseAppError as err:
            return ORJSONResponse(
                status_code=err.status_code,
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
