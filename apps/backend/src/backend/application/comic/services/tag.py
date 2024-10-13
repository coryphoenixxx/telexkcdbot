from collections.abc import Sequence
from dataclasses import dataclass

from backend.application.comic.commands import TagCreateCommand, TagUpdateCommand
from backend.application.comic.interfaces import TagRepoInterface
from backend.application.comic.responses import TagResponseData
from backend.application.common.interfaces import TransactionManagerInterface
from backend.domain.value_objects import TagId


@dataclass(slots=True)
class CreateTagInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: TagCreateCommand) -> TagId:
        tag_id = await self.tag_repo.create(command.to_entity())
        await self.transaction.commit()
        return tag_id


@dataclass(slots=True)
class CreateManyTagsInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, commands: list[TagCreateCommand]) -> Sequence[TagId]:
        tag_ids = await self.tag_repo.create_many([c.to_entity() for c in commands])
        await self.transaction.commit()
        return tag_ids


@dataclass(slots=True)
class UpdateTagInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, command: TagUpdateCommand) -> None:
        tag = await self.tag_repo.load(tag_id=TagId(command["tag_id"]))

        if "name" in command:
            tag.set_name(command["name"])
        if "is_visible" in command:
            tag.is_visible = command["is_visible"]

        await self.tag_repo.update(tag)
        await self.transaction.commit()


@dataclass(slots=True)
class DeleteTagInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, tag_id: TagId) -> None:
        await self.tag_repo.delete(tag_id)
        await self.transaction.commit()


@dataclass(slots=True)
class TagReader:
    tag_repo: TagRepoInterface

    async def get_by_id(self, tag_id: TagId) -> TagResponseData:
        return await self.tag_repo.get_by_id(tag_id)
