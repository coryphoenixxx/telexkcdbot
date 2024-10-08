from dataclasses import dataclass
from enum import StrEnum


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(slots=True)
class Pagination:
    limit: int | None = None
    offset: int | None = None
    order: SortOrder = SortOrder.ASC
