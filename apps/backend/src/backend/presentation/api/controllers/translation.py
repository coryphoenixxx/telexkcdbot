from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from backend.application.comic.services import (
    AddTranslationInteractor,
    DeleteTranslationInteractor,
    TranslationReader,
    UpdateTranslationInteractor,
)
from backend.application.common.exceptions import TempFileNotFoundError
from backend.domain.entities.translation import OriginalTranslationOperationForbiddenError
from backend.domain.value_objects.common import TranslationId
from backend.domain.value_objects.translation_title import TranslationTitleLengthError
from backend.presentation.api.controllers.schemas import (
    TranslationCreateSchema,
    TranslationResponseSchema,
    TranslationUpdateSchema,
)

router = APIRouter(tags=["Translations"], route_class=DishkaRoute)


@router.post(
    "/comics/id:{comic_id}/translations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": TranslationTitleLengthError | OriginalTranslationOperationForbiddenError
        },
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError | TempFileNotFoundError},
        status.HTTP_409_CONFLICT: {"model": TranslationAlreadyExistsError},
    },
)
async def add_translation(
    comic_id: int,
    schema: TranslationCreateSchema,
    *,
    interactor: FromDishka[AddTranslationInteractor],
    reader: FromDishka[TranslationReader],
) -> TranslationResponseSchema:
    translation_id = await interactor.execute(schema.to_command(comic_id))
    return TranslationResponseSchema.from_data(data=await reader.get_by_id(translation_id))


@router.patch(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": TranslationTitleLengthError
            | TempFileNotFoundError
            | OriginalTranslationOperationForbiddenError
        },
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def update_translation(
    translation_id: int,
    schema: TranslationUpdateSchema,
    *,
    interactor: FromDishka[UpdateTranslationInteractor],
    reader: FromDishka[TranslationReader],
) -> TranslationResponseSchema:
    await interactor.execute(command=schema.to_command(translation_id))
    return TranslationResponseSchema.from_data(
        data=await reader.get_by_id(TranslationId(translation_id))
    )


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": OriginalTranslationOperationForbiddenError},
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def delete_translation(
    translation_id: int,
    *,
    interactor: FromDishka[DeleteTranslationInteractor],
) -> None:
    await interactor.execute(TranslationId(translation_id))


@router.get(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def get_translation_by_id(
    translation_id: int,
    *,
    interactor: FromDishka[TranslationReader],
) -> TranslationResponseSchema:
    return TranslationResponseSchema.from_data(
        data=await interactor.get_by_id(TranslationId(translation_id))
    )


@router.get(
    "/translations/{translation_id}/transcript",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def get_translation_transcript(
    translation_id: int,
    *,
    reader: FromDishka[TranslationReader],
) -> str:
    data = await reader.get_by_id(TranslationId(translation_id))
    return data.transcript
