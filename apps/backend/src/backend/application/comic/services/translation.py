from dataclasses import dataclass

from backend.application.comic.commands import TranslationCreateCommand, TranslationUpdateCommand
from backend.application.comic.interfaces import ComicRepoInterface, TranslationRepoInterface
from backend.application.comic.responses import TranslationResponseData
from backend.application.comic.services.mixins import (
    ProcessTranslationImageMixin,
    TranslationImagePathData,
)
from backend.application.common.interfaces import TransactionManagerInterface
from backend.domain.value_objects.common import ImageId, TranslationId


@dataclass(slots=True)
class AddTranslationInteractor(ProcessTranslationImageMixin):
    translation_repo: TranslationRepoInterface
    comic_repo: ComicRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: TranslationCreateCommand) -> TranslationId:
        new_translation, image_ids = command.unpack()

        translation_id = await self.translation_repo.create(new_translation)
        number = await self.comic_repo.get_issue_number_by_id(new_translation.comic_id)
        await self.create_images(
            link_id=translation_id,
            image_ids=image_ids,
            path_data=TranslationImagePathData(
                number=number,
                title=new_translation.title,
                language=new_translation.language,
                status=new_translation.status,
            ),
        )

        await self.transaction.commit()

        await self.postprocess_images_in_background(image_ids)

        return translation_id


@dataclass(slots=True)
class UpdateTranslationInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(
        self,
        command: TranslationUpdateCommand,
    ) -> TranslationId:
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

        created_image_ids: list[ImageId] = []
        if "image_ids" in command:
            image_ids = [ImageId(image_id) for image_id in command["image_ids"]]
            created_image_ids = await self.process_images(
                link_id=translation_id,
                image_ids=image_ids,
                path_data=TranslationImagePathData(
                    number=await self.comic_repo.get_issue_number_by_id(translation.comic_id),
                    title=translation.title,
                    language=translation.language,
                    status=translation.status,
                ),
            )

        await self.transaction.commit()

        await self.postprocess_images_in_background(created_image_ids)

        return translation_id


@dataclass(slots=True)
class DeleteTranslationInteractor:
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, translation_id: TranslationId) -> None:
        await self.translation_repo.delete(translation_id)
        await self.transaction.commit()


@dataclass(slots=True)
class TranslationReader:
    translation_repo: TranslationRepoInterface

    async def get_by_id(self, translation_id: TranslationId) -> TranslationResponseData:
        return await self.translation_repo.get_by_id(translation_id)
