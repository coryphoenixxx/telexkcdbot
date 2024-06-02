from fastapi import Depends
from faststream.nats.fastapi import NatsRouter as APIRouter
from starlette import status

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
from api.infrastructure.database.holder import DatabaseHolder
from api.presentation.stub import Stub
from api.presentation.web.controllers.schemas.requests import (
    TranslationDraftRequestSchema,
    TranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses.translation import (
    TranslationWDraftStatusSchema,
    TranslationWLanguageResponseSchema,
)
from api.types import ComicID, Language, TranslationID

router = APIRouter(tags=["Translations"])


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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await TranslationService(db_holder).add(comic_id, schema.to_dto())

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await TranslationService(db_holder).add(comic_id, schema.to_dto())

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    translation_resp_dto = await TranslationService(db_holder).update(
        translation_id=translation_id,
        dto=schema.to_dto(),
    )

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
):
    await TranslationService(db_holder).delete(translation_id)


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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWDraftStatusSchema:
    translation_resp_dto = await TranslationService(db_holder).get_by_id(translation_id)

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> str:
    translation_resp_dto = await TranslationService(db_holder).get_by_id(translation_id)

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
):
    await TranslationService(db_holder).publish(translation_id)


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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    result = await TranslationService(db_holder).get_by_language(comic_id, language)

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> list[TranslationWLanguageResponseSchema]:
    translation_resp_dtos = await TranslationService(db_holder).get_all(comic_id, False)

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
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> list[TranslationWLanguageResponseSchema]:
    translation_resp_dtos = await TranslationService(db_holder).get_all(comic_id, True)

    return [TranslationWLanguageResponseSchema.from_dto(dto) for dto in translation_resp_dtos]
