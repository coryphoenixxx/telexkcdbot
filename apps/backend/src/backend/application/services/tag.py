from dataclasses import dataclass

from backend.application.dtos import TagResponseDTO
from backend.application.dtos.requests import TagUpdateDTO
from backend.core.value_objects import TagID
from backend.infrastructure.database.repositories.tag import TagRepo
from backend.infrastructure.database.transaction import TransactionManager


@dataclass(slots=True, eq=False, frozen=True)
class TagService:
    transaction: TransactionManager
    repo: TagRepo

    async def update(
        self,
        tag_id: TagID,
        dto: TagUpdateDTO,
    ) -> TagResponseDTO:
        tag = await self.repo.update(tag_id, dto)
        await self.transaction.commit()
        return tag

    async def delete(self, tag_id: TagID) -> None:
        await self.repo.delete(tag_id)
        await self.transaction.commit()
