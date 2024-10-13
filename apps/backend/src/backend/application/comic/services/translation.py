from dataclasses import dataclass

from backend.application.comic.commands import TranslationCreateCommand, TranslationUpdateCommand
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TranslationImagePathData,
    TranslationImageProcessorInterface,
    TranslationRepoInterface,
)
from backend.application.comic.responses import TranslationResponseData
from backend.application.common.interfaces import (
    TransactionManagerInterface,
)
from backend.domain.value_objects.common import ImageId, TranslationId


@dataclass(slots=True)
class AddTranslationInteractor:
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    image_processor: TranslationImageProcessorInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: TranslationCreateCommand) -> TranslationId:
        new_translation, image_ids = command.unpack()

        comic_number, comic_title = await self.comic_repo.get_number_and_title_by_id(
            new_translation.comic_id
        )

        translation_id = await self.translation_repo.create(new_translation)

        await self.image_processor.create_new(
            translation_id=translation_id,
            image_ids=image_ids,
            path_data=TranslationImagePathData(
                number=comic_number,
                original_title=comic_title,
                translation_title=new_translation.title,
                language=new_translation.language,
                status=new_translation.status,
            ),
        )

        await self.transaction.commit()

        await self.image_processor.publish_created()

        return translation_id


@dataclass(slots=True)
class UpdateTranslationInteractor:
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    image_processor: TranslationImageProcessorInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: TranslationUpdateCommand) -> TranslationId:
        translation_id = TranslationId(command["translation_id"])
        translation = await self.translation_repo.load(translation_id)

        if "title" in command:
            translation.set_title(command["title"])
        if "language" in command:
            translation.set_language(command["language"])
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

        await self.translation_repo.update(translation)

        comic_number, comic_title = await self.comic_repo.get_number_and_title_by_id(
            translation.comic_id
        )

        await self.image_processor.update_state(
            translation_id=translation_id,
            image_ids=[ImageId(image_id) for image_id in command["image_ids"]],
            path_data=TranslationImagePathData(
                number=comic_number,
                original_title=comic_title,
                translation_title=translation.title,
                language=translation.language,
                status=translation.status,
            ),
        )

        await self.transaction.commit()

        await self.image_processor.publish_created()

        return translation_id


@dataclass(slots=True)
class DeleteTranslationInteractor:
    translation_repo: TranslationRepoInterface
    image_processor: TranslationImageProcessorInterface
    transaction: TransactionManagerInterface

    async def execute(self, translation_id: TranslationId) -> None:
        await self.translation_repo.delete(translation_id)
        await self.image_processor.delete_linked(translation_id)
        await self.transaction.commit()


@dataclass(slots=True)
class TranslationReader:
    translation_repo: TranslationRepoInterface

    async def get_by_id(self, translation_id: TranslationId) -> TranslationResponseData:
        return await self.translation_repo.get_by_id(translation_id)
