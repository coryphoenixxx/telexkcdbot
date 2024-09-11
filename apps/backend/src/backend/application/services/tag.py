from dataclasses import dataclass

from backend.application.dtos import TagResponseDTO, TagUpdateDTO
from backend.core.value_objects import TagID
from backend.infrastructure.database.repositories.tag import TagRepo
from backend.infrastructure.database.transaction import TransactionManager
from backend.infrastructure.utils import slugify


@dataclass(slots=True, eq=False, frozen=True)
class TagService:
    transaction: TransactionManager
    repo: TagRepo

    async def update(
        self,
        tag_id: TagID,
        dto: TagUpdateDTO,
    ) -> TagResponseDTO:
        data = {**dto}
        if data.get("name"):
            name = dto["name"].value
            data["name"], data["slug"] = name, slugify(name)

        resp_dto = await self.repo.update(tag_id, data)
        await self.transaction.commit()
        return resp_dto

    async def delete(self, tag_id: TagID) -> None:
        await self.repo.delete(tag_id)
        await self.transaction.commit()
