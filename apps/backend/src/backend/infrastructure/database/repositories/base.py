from dataclasses import dataclass
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.models import BaseModel

Model = TypeVar("Model", bound=BaseModel)


class RepoError(Exception): ...


@dataclass(slots=True)
class BaseRepo:
    session: AsyncSession
