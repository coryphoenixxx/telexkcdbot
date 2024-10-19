from dataclasses import dataclass

from backend.application.comic.commands import TranslationCreateCommand, TranslationUpdateCommand
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TranslationImagePathData,
    TranslationImageSaveHelperInterface,
    TranslationRepoInterface,
)
from backend.application.comic.responses import ComicResponseData, TranslationResponseData
from backend.application.common.interfaces import (
    ConvertImageMessage,
    PublisherRouterInterface,
    TransactionManagerInterface,
)
from backend.domain.entities import TranslationEntity
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import TranslationTitle
from backend.domain.value_objects.common import ImageId, IssueNumber, TranslationId


@dataclass(slots=True)
class AddTranslationInteractor:
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface
    publisher: PublisherRouterInterface

    async def execute(self, command: TranslationCreateCommand) -> TranslationId:
        new_translation, image_id = command.unpack()

        comic_data: ComicResponseData = await self.comic_repo.get_by(new_translation.comic_id)

        translation_id = await self.translation_repo.create(new_translation)

        if image_id:
            await self.image_saver.create_new_image(
                translation_id=translation_id,
                image_id=image_id,
                path_data=TranslationImagePathData(
                    number=cast_or_none(IssueNumber, comic_data.number),
                    original_title_slug=TranslationTitle(comic_data.title).slug,
                    translation_title_slug=new_translation.title.slug,
                    language=new_translation.language,
                    status=new_translation.status,
                ),
            )

        await self.transaction.commit()

        if image_id:
            await self.publisher.publish(ConvertImageMessage(image_id=image_id.value))

        return translation_id


@dataclass(slots=True)
class UpdateTranslationInteractor:
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface
    publisher: PublisherRouterInterface

    async def execute(self, command: TranslationUpdateCommand) -> TranslationId:
        translation_id = TranslationId(command["translation_id"])

        translation = await self.translation_repo.load(translation_id)

        move_image_required = False
        if "title" in command:
            translation.set_title(command["title"])
        if "language" in command:
            translation.set_language(command["language"])
            move_image_required = True
        if "tooltip" in command:
            translation.tooltip = command["tooltip"]
        if "transcript" in command:
            translation.transcript = command["transcript"]
        if "translator_comment" in command:
            translation.translator_comment = command["translator_comment"]
        if "source_url" in command:
            translation.source_url = command["source_url"]
        if "status" in command:
            translation.status = command["status"]
            move_image_required = True

        await self.translation_repo.update(translation)

        created_image_id = await self._handle_image_update(
            translation, command, move_image_required
        )

        await self.transaction.commit()

        if created_image_id:
            await self.publisher.publish(ConvertImageMessage(image_id=created_image_id.value))

        return translation_id

    async def _handle_image_update(
        self,
        translation: TranslationEntity,
        command: TranslationUpdateCommand,
        move_image_required: bool,
    ) -> ImageId | None:
        created_image_id: ImageId | None = None

        if "image_id" in command:
            request_image_id = command["image_id"]

            comic_data: ComicResponseData = await self.comic_repo.get_by(translation.comic_id)

            created_image_id = await self.image_saver.update_image(
                translation_id=translation.id,
                old_image_id=await self.image_saver.get_linked_image_id(translation.id),
                new_image_id=cast_or_none(ImageId, request_image_id),
                path_data=TranslationImagePathData(
                    number=cast_or_none(IssueNumber, comic_data.number),
                    original_title_slug=TranslationTitle(comic_data.title).slug,
                    translation_title_slug=translation.title.slug,
                    language=translation.language,
                    status=translation.status,
                ),
                move_image_required=move_image_required,
            )

        return created_image_id


@dataclass(slots=True)
class DeleteTranslationInteractor:
    translation_repo: TranslationRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface

    async def execute(self, translation_id: TranslationId) -> None:
        await self.translation_repo.delete(translation_id)
        linked_image_id = await self.image_saver.get_linked_image_id(translation_id)
        await self.image_saver.soft_delete_image(linked_image_id)
        await self.transaction.commit()


@dataclass(slots=True)
class TranslationReader:
    translation_repo: TranslationRepoInterface

    async def get_by_id(self, translation_id: TranslationId) -> TranslationResponseData:
        return await self.translation_repo.get_by_id(translation_id)
