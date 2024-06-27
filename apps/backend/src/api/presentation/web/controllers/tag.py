from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from api.application.dtos.common import TagName
from api.application.services.tag import TagService
from api.core.exceptions.tag import TagNotFoundError
from api.core.value_objects import TagID
from api.presentation.web.controllers.schemas.responses import TagResponseWBlacklistStatusSchema

router = APIRouter(tags=["Tags"], route_class=DishkaRoute)


@router.put(
    "/comics/tags/{tag_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TagNotFoundError},
    },
)
async def update_tag(
    tag_id: TagID,
    name: TagName,
    blacklist_status: bool,
    *,
    service: Depends[TagService],
) -> TagResponseWBlacklistStatusSchema:
    return TagResponseWBlacklistStatusSchema.from_dto(
        dto=await service.update(tag_id, name, blacklist_status)
    )


@router.delete(
    "/comics/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    tag_id: TagID,
    *,
    service: Depends[TagService],
) -> None:
    await service.delete(tag_id=tag_id)
