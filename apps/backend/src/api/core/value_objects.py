from typing import Annotated, NewType
from uuid import UUID

from annotated_types import Gt

ComicID = NewType("ComicID", Annotated[int, Gt(0)])
TagID = NewType("TagID", Annotated[int, Gt(0)])
IssueNumber = NewType("IssueNumber", Annotated[int, Gt(0)])
TranslationID = NewType("TranslationID", Annotated[int, Gt(0)])
TranslationImageID = NewType("TranslationImageID", Annotated[int, Gt(0)])
TempImageUUID = NewType("TempImageID", UUID)
