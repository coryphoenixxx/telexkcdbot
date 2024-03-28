import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import NewType


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(slots=True)
class DateRange:
    start: datetime.date | None
    end: datetime.date | None


Limit = NewType("Limit", int)
Offset = NewType("Offset", int)


@dataclass(slots=True)
class QueryParams:
    limit: Limit
    offset: Offset
    date_range: DateRange
    order: Order


@dataclass(slots=True)
class CountMetadata:
    comic_count: int
    translation_count: int
    draft_count: int
    tag_count: int
