from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    OriginalTranslationOperationForbiddenError,
    TempImageNotFoundError,
    TranslationAlreadyExistsError,
    TranslationIsAlreadyPublishedError,
    TranslationNotFoundError,
)
from backend.application.comic.services import (
    AddTranslationInteractor,
    DeleteTranslationDraftInteractor,
    FullUpdateTranslationInteractor,
    PublishTranslationDraftInteractor,
    TranslationReader,
)
from backend.core.value_objects import ComicID, Language, TranslationID
from backend.presentation.api.controllers.schemas import (
    TranslationDraftRequestSchema,
    TranslationRequestSchema,
    TranslationWDraftStatusSchema,
    TranslationWLanguageResponseSchema,
)

router = APIRouter(tags=["Translations"], route_class=DishkaRoute)


@router.post(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": TempImageNotFoundError | OriginalTranslationOperationForbiddenError
        },
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
        status.HTTP_409_CONFLICT: {"model": TranslationAlreadyExistsError},
    },
)
async def add_translation(
    comic_id: int,
    schema: TranslationRequestSchema,
    *,
    service: FromDishka[AddTranslationInteractor],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.execute(ComicID(comic_id), schema.to_dto())
    )


@router.post(
    "/comics/{comic_id}/translation-drafts",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": TempImageNotFoundError | OriginalTranslationOperationForbiddenError
        },
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def add_translation_draft(
    comic_id: int,
    schema: TranslationDraftRequestSchema,
    *,
    service: FromDishka[AddTranslationInteractor],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.execute(ComicID(comic_id), schema.to_dto())
    )


@router.post(
    "/translations/{translation_id}/publish",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
        status.HTTP_409_CONFLICT: {"model": TranslationIsAlreadyPublishedError},
    },
)
async def publish_translation_draft(
    translation_id: int,
    *,
    service: FromDishka[PublishTranslationDraftInteractor],
) -> None:
    await service.execute(TranslationID(translation_id))


@router.put(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": TempImageNotFoundError | OriginalTranslationOperationForbiddenError
        },
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def update_translation(
    translation_id: int,
    schema: TranslationRequestSchema,
    *,
    service: FromDishka[FullUpdateTranslationInteractor],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.execute(TranslationID(translation_id), schema.to_dto())
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
    service: FromDishka[DeleteTranslationDraftInteractor],
) -> None:
    await service.execute(TranslationID(translation_id))


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
    service: FromDishka[TranslationReader],
) -> TranslationWDraftStatusSchema:
    return TranslationWDraftStatusSchema.from_dto(
        dto=await service.get_by_id(TranslationID(translation_id))
    )


@router.get(
    "/translations/{translation_id}/raw_transcript",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def get_translation_raw_transcript(
    translation_id: int,
    *,
    service: FromDishka[TranslationReader],
) -> str:
    dto = await service.get_by_id(TranslationID(translation_id))
    return dto.raw_transcript


@router.get(
    "/comics/{comic_id}/translations/{language}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationNotFoundError},
    },
)
async def get_translation_by_language(
    comic_id: int,
    language: Language,
    *,
    service: FromDishka[TranslationReader],
) -> TranslationWLanguageResponseSchema:
    dto = await service.get_by_language(ComicID(comic_id), language)
    return TranslationWLanguageResponseSchema.from_dto(dto)
