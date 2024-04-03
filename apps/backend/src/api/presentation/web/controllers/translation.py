from fastapi import Depends
from faststream.nats.fastapi import NatsRouter
from starlette import status

from api.application.exceptions.translation import (
    EnglishTranslationCreateForbiddenError,
    TranslationAlreadyExistsError,
    TranslationImagesAlreadyAttachedError,
    TranslationImagesNotCreatedError,
    TranslationNotFoundError,
)
from api.application.services import TranslationService
from api.application.types import TranslationID
from api.infrastructure.database.holder import DatabaseHolder
from api.presentation.stub import Stub
from api.presentation.web.controllers.schemas.requests import (
    TranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses.translation import (
    TranslationWLanguageResponseSchema,
)

router = NatsRouter(tags=["Translations"])


@router.post(
    "/translations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": EnglishTranslationCreateForbiddenError},
        status.HTTP_409_CONFLICT: {
            "model": TranslationAlreadyExistsError
            | TranslationImagesNotCreatedError
            | TranslationImagesAlreadyAttachedError,
        },
    },
)
async def add_translation(
    schema: TranslationRequestSchema,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    # TODO: deny EN translation draft creation
    translation_resp_dto = await TranslationService(db_holder).create(schema.to_dto())

    return TranslationWLanguageResponseSchema.from_dto(translation_resp_dto)


@router.put(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": TranslationNotFoundError,
        },
        status.HTTP_409_CONFLICT: {
            "model": TranslationImagesNotCreatedError | TranslationImagesAlreadyAttachedError,
        },
    },
)
async def update_translation(
    translation_id: TranslationID,
    schema: TranslationRequestSchema,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
) -> TranslationWLanguageResponseSchema:
    # TODO: need comic_id in schema?
    translation_resp_dto = await TranslationService(
        db_holder=db_holder,
    ).update(translation_id, schema.to_dto())

    return TranslationWLanguageResponseSchema.from_dto(translation_resp_dto)


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": TranslationNotFoundError,
        },
    },
)
async def delete_translation(
    translation_id: TranslationID,
    *,
    db_holder: DatabaseHolder = Depends(Stub(DatabaseHolder)),
):
    # TODO: deny EN translation deletion
    await TranslationService(db_holder=db_holder).delete(translation_id)
