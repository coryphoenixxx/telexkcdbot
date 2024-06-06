from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from api.application.dtos.common import Language
from api.application.exceptions.comic import ComicByIDNotFoundError
from api.application.exceptions.translation import (
    ImagesAlreadyAttachedError,
    ImagesNotCreatedError,
    OriginalTranslationOperationForbiddenError,
    TranslationAlreadyExistsError,
    TranslationByIDNotFoundError,
    TranslationByLanguageNotFoundError,
)
from api.application.services import TranslationService
from api.core.entities import ComicID, TranslationID
from api.presentation.web.controllers.schemas.requests import (
    TranslationDraftRequestSchema,
    TranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses import (
    TranslationWDraftStatusSchema,
    TranslationWLanguageResponseSchema,
)

router = APIRouter(tags=["Translations"], route_class=DishkaRoute)


@router.post(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicByIDNotFoundError},
        status.HTTP_409_CONFLICT: {
            "model": TranslationAlreadyExistsError
            | ImagesNotCreatedError
            | ImagesAlreadyAttachedError,
        },
    },
)
async def add_translation(
    comic_id: ComicID,
    schema: TranslationRequestSchema,
    *,
    service: Depends[TranslationService],
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await service.add(comic_id, schema.to_dto())

    return TranslationWLanguageResponseSchema.from_dto(translation_resp_dto)


@router.post(
    "/comics/{comic_id}/translation-drafts",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicByIDNotFoundError},
        status.HTTP_409_CONFLICT: {
            "model": ImagesNotCreatedError | ImagesAlreadyAttachedError,
        },
    },
)
async def add_translation_draft(
    comic_id: ComicID,
    schema: TranslationDraftRequestSchema,
    *,
    service: Depends[TranslationService],
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await service.add(comic_id, schema.to_dto())

    return TranslationWLanguageResponseSchema.from_dto(translation_resp_dto)


@router.put(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": OriginalTranslationOperationForbiddenError},
        status.HTTP_404_NOT_FOUND: {"model": TranslationByIDNotFoundError},
        status.HTTP_409_CONFLICT: {
            "model": ImagesNotCreatedError | ImagesAlreadyAttachedError,
        },
    },
)
async def update_translation(
    translation_id: TranslationID,
    schema: TranslationRequestSchema,
    *,
    service: Depends[TranslationService],
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await service.update(translation_id, schema.to_dto())

    return TranslationWLanguageResponseSchema.from_dto(translation_resp_dto)


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": OriginalTranslationOperationForbiddenError},
        status.HTTP_404_NOT_FOUND: {"model": TranslationByIDNotFoundError},
    },
)
async def delete_translation(
    translation_id: TranslationID,
    *,
    service: Depends[TranslationService],
):
    await service.delete(translation_id)


@router.get(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationByIDNotFoundError},
    },
)
async def get_translation_by_id(
    translation_id: TranslationID,
    *,
    service: Depends[TranslationService],
) -> TranslationWDraftStatusSchema:
    translation_resp_dto = await service.get_by_id(translation_id)

    return TranslationWDraftStatusSchema.from_dto(translation_resp_dto)


@router.get(
    "/translations/{translation_id}/raw_transcript",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationByIDNotFoundError},
    },
)
async def get_translation_raw_transcript(
    translation_id: TranslationID,
    *,
    service: Depends[TranslationService],
) -> str:
    translation_resp_dto = await service.get_by_id(translation_id)

    return translation_resp_dto.raw_transcript


@router.post(
    "/translations/{translation_id}/publish",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationByIDNotFoundError},
    },
)
async def publish_draft(
    translation_id: TranslationID,
    *,
    service: Depends[TranslationService],
):
    await service.publish(translation_id)


@router.get(
    "/comics/{comic_id}/translations/{language}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": TranslationByLanguageNotFoundError},
    },
)
async def get_translation_by_language(
    comic_id: ComicID,
    language: Language,
    *,
    service: Depends[TranslationService],
) -> TranslationWLanguageResponseSchema:
    result = await service.get_by_language(comic_id, language)

    return TranslationWLanguageResponseSchema.from_dto(result)


@router.get(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicByIDNotFoundError},
    },
)
async def get_comic_translations(
    comic_id: ComicID,
    *,
    service: Depends[TranslationService],
) -> list[TranslationWLanguageResponseSchema]:
    translation_resp_dtos = await service.get_all(comic_id, False)

    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in translation_resp_dtos]


@router.get(
    "/comics/{comic_id}/translation-drafts",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ComicByIDNotFoundError},
    },
)
async def get_comic_translation_drafts(
    comic_id: ComicID,
    *,
    service: Depends[TranslationService],
) -> list[TranslationWLanguageResponseSchema]:
    translation_resp_dtos = await service.get_all(comic_id, True)

    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in translation_resp_dtos]
