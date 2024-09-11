from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from starlette import status

from backend.application.services.tag import TagService
from backend.core.value_objects import TagID
from backend.infrastructure.database.repositories.tag import TagNotFoundError
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
    service: FromDishka[TagService],
) -> TagResponseWBlacklistStatusSchema:
    return TagResponseWBlacklistStatusSchema.from_dto(
        dto=await service.update(TagID(tag_id), schema.to_dto())
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
    service: FromDishka[TagService],
) -> None:
    await service.delete(tag_id=TagID(tag_id))
