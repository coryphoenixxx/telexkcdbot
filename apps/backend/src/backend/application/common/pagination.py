import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

from annotated_types import Ge

from backend.core.value_objects import TagName

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])
Limit = NewType("Limit", Annotated[int, Ge(0)])
Offset = NewType("Offset", Annotated[int, Ge(0)])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class TagParam(StrEnum):
    AND = "AND"
    OR = "OR"


@dataclass(slots=True)
class DateRange:
    start: datetime.date | None
    end: datetime.date | None


@dataclass(slots=True)
class ComicFilterParams:
    q: str | None = None
    limit: Limit | None = None
    offset: Offset | None = None
    date_range: DateRange | None = None
    order: Order | None = None
    tags: list[TagName] | None = None
    tag_param: TagParam | None = None
