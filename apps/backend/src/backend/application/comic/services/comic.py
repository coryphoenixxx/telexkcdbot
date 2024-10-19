from collections.abc import Sequence
from dataclasses import dataclass

from backend.application.comic.commands import ComicCreateCommand, ComicUpdateCommand
from backend.application.comic.filters import ComicFilters
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TranslationImagePathData,
    TranslationImageSaveHelperInterface,
)
from backend.application.comic.responses import (
    ComicCompactResponseData,
    ComicResponseData,
    TranslationResponseData,
)
from backend.application.common.interfaces import (
    ConvertImageMessage,
    PublisherRouterInterface,
    TransactionManagerInterface,
)
from backend.application.common.pagination import Pagination
from backend.domain.entities import ComicEntity, TranslationStatus
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import (
    ComicId,
    ImageId,
    IssueNumber,
    Language,
    TagId,
    TranslationId,
    TranslationTitle,
)


@dataclass(slots=True)
class CreateComicInteractor:
    comic_repo: ComicRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface
    publisher: PublisherRouterInterface

    async def execute(self, command: ComicCreateCommand) -> ComicId:
        new_comic, tag_ids, image_id = command.unpack()

        comic_id, original_translation_id = await self.comic_repo.create(new_comic)
        await self.comic_repo.relink_tags(comic_id, tag_ids)

        if image_id:
            title_slug = new_comic.title.slug
            await self.image_saver.create_new_image(
                translation_id=original_translation_id,
                image_id=image_id,
                path_data=TranslationImagePathData(
                    number=new_comic.number,
                    original_title_slug=title_slug,
                    translation_title_slug=title_slug,
                ),
            )

        await self.transaction.commit()

        if image_id:
            await self.publisher.publish(ConvertImageMessage(image_id=image_id.value))

        return comic_id


@dataclass(slots=True)
class UpdateComicInteractor:
    comic_repo: ComicRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface
    publisher: PublisherRouterInterface

    async def execute(self, command: ComicUpdateCommand) -> None:
        comic_id = ComicId(command["comic_id"])

        comic = await self.comic_repo.load(comic_id)

        move_image_required = False
        if "number" in command:
            comic.set_number(command["number"])
            move_image_required = True
        if "title" in command:
            comic.set_title(command["title"])
            move_image_required = True
        if "tooltip" in command:
            comic.tooltip = command["tooltip"]
        if "click_url" in command:
            comic.click_url = command["click_url"]
        if "explain_url" in command:
            comic.explain_url = command["explain_url"]
        if "is_interactive" in command:
            comic.is_interactive = command["is_interactive"]
        if "transcript" in command:
            comic.transcript = command["transcript"]

        await self.comic_repo.update(comic)

        if "tag_ids" in command:
            tag_ids = [TagId(tag_id) for tag_id in command["tag_ids"]]
            await self.comic_repo.relink_tags(comic_id, tag_ids)

        created_image_id = await self._handle_image_update(comic, command, move_image_required)

        await self.transaction.commit()

        if created_image_id:
            await self.publisher.publish(ConvertImageMessage(image_id=created_image_id.value))

    async def _handle_image_update(
        self,
        comic: ComicEntity,
        command: ComicUpdateCommand,
        move_image_required: bool,
    ) -> ImageId | None:
        created_image_id: ImageId | None = None

        if "image_id" in command:
            request_image_id = command["image_id"]

            old_image_id = await self.image_saver.get_linked_image_id(comic.original_translation_id)
            new_image_id = cast_or_none(ImageId, request_image_id)
            comic_slug = comic.title.slug

            created_image_id = await self.image_saver.update_image(
                translation_id=comic.original_translation_id,
                old_image_id=old_image_id,
                new_image_id=new_image_id,
                path_data=TranslationImagePathData(
                    number=comic.number,
                    original_title_slug=comic_slug,
                    translation_title_slug=comic_slug,
                ),
                move_image_required=move_image_required,
            )

            if old_image_id == new_image_id and move_image_required:
                translations = await self.comic_repo.get_translations(comic.id)
                for translation in translations:
                    if translation.image:
                        await self.image_saver.move_image(
                            image_id=ImageId(translation.image.id),
                            new_path_data=TranslationImagePathData(
                                number=comic.number,
                                original_title_slug=comic_slug,
                                translation_title_slug=TranslationTitle(translation.title).slug,
                                language=translation.language,
                                status=translation.status,
                            ),
                        )

        return created_image_id


@dataclass(slots=True)
class DeleteComicInteractor:
    comic_repo: ComicRepoInterface
    image_saver: TranslationImageSaveHelperInterface
    transaction: TransactionManagerInterface

    async def execute(self, comic_id: ComicId) -> None:
        comic = await self.comic_repo.load(comic_id)

        linked_image_id = await self.image_saver.get_linked_image_id(comic.original_translation_id)
        await self.image_saver.soft_delete_image(linked_image_id)

        for translation in await self.comic_repo.get_translations(comic_id):
            linked_image_id = await self.image_saver.get_linked_image_id(
                translation_id=TranslationId(translation.id)
            )
            await self.image_saver.soft_delete_image(linked_image_id)

        await self.comic_repo.delete(comic_id)
        await self.transaction.commit()


@dataclass(slots=True)
class ComicReader:
    comic_repo: ComicRepoInterface

    async def get_by_id(self, comic_id: ComicId) -> ComicResponseData:
        return await self.comic_repo.get_by(comic_id)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseData:
        return await self.comic_repo.get_by(number)

    async def get_by_slug(self, slug: str) -> ComicResponseData:
        return await self.comic_repo.get_by(slug)

    async def get_latest_issue_number(self) -> IssueNumber | None:
        return await self.comic_repo.get_latest_issue_number()

    async def get_list(
        self,
        filters: ComicFilters,
        pagination: Pagination,
    ) -> tuple[int, Sequence[ComicCompactResponseData]]:
        return await self.comic_repo.get_list(filters, pagination)

    async def get_translations(
        self,
        comic_id: ComicId,
        language: Language | None,
        status: TranslationStatus | None,
    ) -> list[TranslationResponseData]:
        return await self.comic_repo.get_translations(comic_id, language, status)
