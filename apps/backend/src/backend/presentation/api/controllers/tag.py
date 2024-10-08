from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from backend.application.comic.exceptions import TagNameAlreadyExistsError, TagNotFoundError
from backend.application.comic.services import (
    CreateTagInteractor,
    DeleteTagInteractor,
    TagReader,
    UpdateTagInteractor,
)
from backend.domain.value_objects import TagId
from backend.domain.value_objects.tag_name import TagNameLengthError
from backend.presentation.api.controllers.schemas import (
    TagCreateSchema,
    TagResponseSchema,
    TagUpdateSchema,
)

router = APIRouter(tags=["Tags"], route_class=DishkaRoute)


@router.post(
    "/tags",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": TagNameLengthError},
        status.HTTP_409_CONFLICT: {"model": TagNameAlreadyExistsError},
    },
)
async def create_tag(
    schema: TagCreateSchema,
    *,
    interactor: FromDishka[CreateTagInteractor],
    reader: FromDishka[TagReader],
) -> TagResponseSchema:
    tag_id = await interactor.execute(schema.to_command())
    return TagResponseSchema.from_data(data=await reader.get_by_id(tag_id))


@router.patch(
    "/tags/{tag_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": TagNameLengthError},
        status.HTTP_404_NOT_FOUND: {"model": TagNotFoundError},
        status.HTTP_409_CONFLICT: {"model": TagNameAlreadyExistsError},
    },
)
async def update_tag(
    tag_id: int,
    schema: TagUpdateSchema,
    *,
    interactor: FromDishka[UpdateTagInteractor],
    reader: FromDishka[TagReader],
) -> TagResponseSchema:
    await interactor.execute(schema.to_command(tag_id))
    return TagResponseSchema.from_data(data=await reader.get_by_id(TagId(tag_id)))


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    tag_id: int,
    *,
    interactor: FromDishka[DeleteTagInteractor],
) -> None:
    await interactor.execute(tag_id=TagId(tag_id))


@router.get(
    "/tags/id:{tag_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TagNotFoundError},
    },
)
async def get_tag(
    tag_id: int,
    *,
    reader: FromDishka[TagReader],
) -> TagResponseSchema:
    return TagResponseSchema.from_data(data=await reader.get_by_id(TagId(tag_id)))
