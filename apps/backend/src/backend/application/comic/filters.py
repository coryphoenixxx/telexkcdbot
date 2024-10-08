import datetime
from dataclasses import dataclass, field
from enum import StrEnum

from backend.domain.value_objects import Language


class TagCombination(StrEnum):
    AND = "AND"
    OR = "OR"


@dataclass(slots=True)
class DateRange:
    start: datetime.date | None = None
    end: datetime.date | None = None


@dataclass(slots=True, kw_only=True)
class ComicFilters:
    search_query: str | None = None
    search_language: Language = Language.EN
    date_range: DateRange = field(default_factory=DateRange)
    tag_slugs: list[str] = field(default_factory=list)
    tag_combination: TagCombination = TagCombination.AND
