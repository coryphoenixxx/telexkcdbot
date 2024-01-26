from dataclasses import dataclass
from enum import StrEnum


class Language(StrEnum):
    EN = "EN"
    RU = "RU"


@dataclass
class Dimensions:
    width: int
    height: int
