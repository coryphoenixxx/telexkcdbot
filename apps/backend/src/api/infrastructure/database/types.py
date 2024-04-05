import datetime
from dataclasses import dataclass
from typing import Annotated, NewType

from annotated_types import Ge
from shared.types import Order

Limit = NewType("Limit", Annotated[int, Ge(0)])
Offset = NewType("Offset", Annotated[int, Ge(0)])


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
