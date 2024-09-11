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
from backend.application.comic.services.comic import (
    ComicDeleteService,
    ComicReadService,
    ComicWriteService,
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
    service: FromDishka[ComicWriteService],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.add_translation(ComicID(comic_id), schema.to_dto())
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
    service: FromDishka[ComicWriteService],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.add_translation(ComicID(comic_id), schema.to_dto())
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
    service: FromDishka[ComicWriteService],
) -> None:
    await service.publish_translation_draft(TranslationID(translation_id))


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
    service: FromDishka[ComicWriteService],
) -> TranslationWLanguageResponseSchema:
    return TranslationWLanguageResponseSchema.from_dto(
        dto=await service.update_translation(TranslationID(translation_id), schema.to_dto())
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
    service: FromDishka[ComicDeleteService],
) -> None:
    await service.delete_translation(TranslationID(translation_id))


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
    service: FromDishka[ComicReadService],
) -> TranslationWDraftStatusSchema:
    return TranslationWDraftStatusSchema.from_dto(
        dto=await service.get_translation_by_id(TranslationID(translation_id))
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
    service: FromDishka[ComicReadService],
) -> str:
    dto = await service.get_translation_by_id(TranslationID(translation_id))
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
    service: FromDishka[ComicReadService],
) -> TranslationWLanguageResponseSchema:
    dto = await service.get_translation_by_language(ComicID(comic_id), language)
    return TranslationWLanguageResponseSchema.from_dto(dto)


@router.get(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicNotFoundError},
    },
)
async def get_comic_translations(
    comic_id: int,
    *,
    service: FromDishka[ComicReadService],
) -> list[TranslationWLanguageResponseSchema]:
    dtos = await service.get_translations(ComicID(comic_id))
    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in dtos]
