from fastapi import APIRouter
from starlette import status
from starlette.responses import RedirectResponse

from backend.presentation.api.controllers.schemas import OKResponseSchema

router = APIRouter(prefix="")


@router.get("/", include_in_schema=False)
async def default_redirect() -> RedirectResponse:
    return RedirectResponse(
        "/docs",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/healthcheck",
    tags=["Healthcheck"],
    status_code=status.HTTP_200_OK,
)
async def healthcheck() -> OKResponseSchema:
    return OKResponseSchema(message="API is available.")
