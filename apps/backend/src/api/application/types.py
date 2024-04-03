from typing import Annotated, NewType

from annotated_types import Ge, Gt

TranslationImageID = NewType("TranslationImageID", Annotated[int, Gt(0)])
ComicID = NewType("ComicID", Annotated[int, Gt(0)])
IssueNumber = NewType("IssueNumber", Annotated[int, Gt(0)])
TranslationID = NewType("TranslationID", Annotated[int, Gt(0)])
TranslationDraftID = NewType("TranslationDraftID", Annotated[int, Gt(0)])

TotalCount = NewType("TotalCount", Annotated[int, Ge(0)])
Limit = NewType("Limit", Annotated[int, Ge(0)])
Offset = NewType("Offset", Annotated[int, Ge(0)])
