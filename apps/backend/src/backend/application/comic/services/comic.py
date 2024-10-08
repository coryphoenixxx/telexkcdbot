from collections.abc import Sequence
from dataclasses import dataclass

from backend.application.comic.commands import ComicCreateCommand, ComicUpdateCommand
from backend.application.comic.filters import ComicFilters
from backend.application.comic.interfaces import (
    ComicRepoInterface,
    TranslationRepoInterface,
)
from backend.application.comic.responses import (
    ComicCompactResponseData,
    ComicResponseData,
    TranslationResponseData,
)
from backend.application.comic.services.mixins import (
    ProcessTranslationImageMixin,
    TranslationImagePathData,
)
from backend.application.common.interfaces import (
    TransactionManagerInterface,
)
from backend.application.common.pagination import Pagination
from backend.domain.entities import ImageLinkType, TranslationStatus
from backend.domain.value_objects import (
    ComicId,
    ImageId,
    IssueNumber,
    Language,
    TagId,
    TranslationId,
)


@dataclass(slots=True)
class CreateComicInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: ComicCreateCommand) -> ComicId:
        new_comic, tag_ids, image_ids = command.unpack()

        comic_id, original_translation_id = await self.comic_repo.create(new_comic)
        await self.comic_repo.relink_tags(comic_id, tag_ids)
        await self.create_images(
            link_id=original_translation_id,
            image_ids=image_ids,
            path_data=TranslationImagePathData(
                number=new_comic.number,
                title=new_comic.title,
                language=Language.EN,
                status=TranslationStatus.PUBLISHED,
            ),
        )

        await self.transaction.commit()

        await self.postprocess_images_in_background(image_ids)

        return comic_id


@dataclass(slots=True)
class UpdateComicInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: ComicUpdateCommand) -> None:
        comic_id = ComicId(command["comic_id"])
        comic = await self.comic_repo.load(comic_id)

        # TODO: rename_images_flag = False
        if "title" in command:
            comic.set_title(command["title"])
        if "tooltip" in command:
            comic.tooltip = command["tooltip"]
        if "click_url" in command:
            comic.explain_url = command["click_url"]
        if "explain_url" in command:
            comic.explain_url = command["explain_url"]
        if "is_interactive" in command:
            comic.is_interactive = command["is_interactive"]
        if "transcript" in command:
            comic.transcript = command["transcript"]

        await self.comic_repo.update(comic)

        if "tag_ids" in command:
            tag_ids = [TagId(tag_id) for tag_id in command["tag_ids"]]
            await self.comic_repo.relink_tags(
                comic_id=comic_id,
                tag_ids=tag_ids,
            )

        created_image_ids: list[ImageId] = []
        if "image_ids" in command:
            image_ids = [ImageId(image_id) for image_id in command["image_ids"]]
            created_image_ids.extend(
                await self.process_images(
                    link_id=comic.original_translation_id,
                    image_ids=image_ids,
                    path_data=TranslationImagePathData(
                        number=comic.number,
                        title=comic.title,
                        language=Language.EN,
                        status=TranslationStatus.PUBLISHED,
                    ),
                )
            )

        await self.transaction.commit()

        await self.postprocess_images_in_background(created_image_ids)


@dataclass(slots=True)
class DeleteComicInteractor(ProcessTranslationImageMixin):
    comic_repo: ComicRepoInterface
    translation_repo: TranslationRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, comic_id: ComicId) -> None:
        translations = await self.comic_repo.get_translations(comic_id)

        to_delete_image_ids: list[ImageId] = []
        for translation in translations:
            linked_image_ids = await self.image_repo.get_linked_image_ids(
                link_type=ImageLinkType.TRANSLATION,
                link_id=TranslationId(translation.id),
            )
            to_delete_image_ids.extend(linked_image_ids)

        await self.delete_images(to_delete_image_ids)
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
