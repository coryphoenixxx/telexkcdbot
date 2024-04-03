import datetime
from dataclasses import dataclass
from enum import StrEnum

from api.application.types import Limit, Offset


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(slots=True)
class DateRange:
    start: datetime.date | None
    end: datetime.date | None


@dataclass(slots=True)
class ComicFilterParams:
    limit: Limit
    offset: Offset
    date_range: DateRange
    order: Order


@dataclass(slots=True)
class CountMetadata:
    comic_count: int
