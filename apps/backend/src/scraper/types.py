from dataclasses import dataclass


@dataclass(slots=True)
class LimitParams:
    start: int
    end: int
    chunk_size: int
    delay: int
