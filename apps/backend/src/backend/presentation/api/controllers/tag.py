from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from starlette import status

from backend.application.comic.exceptions import TagNotFoundError
from backend.application.comic.services import DeleteTagInteractor, UpdateTagInteractor
from backend.core.value_objects import TagID
from backend.presentation.api.controllers.schemas import (
    TagResponseWBlacklistStatusSchema,
    TagUpdateQuerySchema,
)

router = APIRouter(tags=["Tags"], route_class=DishkaRoute)


@router.patch(
    "/comics/tags/{tag_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TagNotFoundError},
    },
)
async def update_tag(
    tag_id: int,
    schema: TagUpdateQuerySchema = Depends(),
    *,
    service: FromDishka[UpdateTagInteractor],
) -> TagResponseWBlacklistStatusSchema:
    return TagResponseWBlacklistStatusSchema.from_dto(
        dto=await service.execute(TagID(tag_id), schema.to_dto())
    )


@router.delete(
    "/comics/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TagNotFoundError},
    },
)
async def delete_tag(
    tag_id: int,
    *,
    service: FromDishka[DeleteTagInteractor],
) -> None:
    await service.execute(tag_id=TagID(tag_id))
