from api.application.dtos.common import Language
from api.application.dtos.requests import TranslationRequestDTO
from api.application.dtos.responses import TranslationResponseDTO
from api.application.exceptions.translation import (
    OriginalTranslationOperationForbiddenError,
)
from api.core.entities import ComicID, TranslationID
from api.infrastructure.database.gateways import ComicGateway, TranslationGateway
from api.infrastructure.database.uow import UnitOfWork


class TranslationService:
    def __init__(
        self,
        uow: UnitOfWork,
        translation_gateway: TranslationGateway,
        comic_gateway: ComicGateway,
    ):
        self._uow = uow
        self._comic_gateway = comic_gateway
        self._translation_gateway = translation_gateway

    async def add(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self._translation_gateway.add(comic_id, dto)

        await self._uow.commit()

        return translation

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        if dto.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        candidate = await self._translation_gateway.get_by_id(translation_id)

        if candidate.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        translation = await self._translation_gateway.update(translation_id=translation_id, dto=dto)

        await self._uow.commit()

        return translation

    async def delete(self, translation_id: TranslationID) -> None:
        translation = await self._translation_gateway.get_by_id(translation_id)

        if translation.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

        await self._translation_gateway.delete(translation_id)

        await self._uow.commit()

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return await self._translation_gateway.get_by_id(translation_id)

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO:
        return await self._translation_gateway.get_by_language(comic_id, language)

    async def get_all(
        self,
        comic_id: ComicID,
        is_draft: bool = False,
    ) -> list[TranslationResponseDTO]:
        draft_resp_dtos = await self._comic_gateway.get_translations(comic_id, is_draft)

        return draft_resp_dtos

    async def publish(self, translation_id: TranslationID):
        candidate = await self._translation_gateway.get_by_id(translation_id)

        if candidate.is_draft:
            published_translations = await self._comic_gateway.get_translations(
                comic_id=candidate.comic_id,
            )

            published = None
            for tr in published_translations:
                if tr.language == candidate.language:
                    published = await self._translation_gateway.get_by_id(tr.id)
                    break

            if published:
                await self._translation_gateway.update_draft_status(published.id, True)

            await self._translation_gateway.update_draft_status(candidate.id, False)

            await self._uow.commit()
