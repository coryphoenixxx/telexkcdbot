from dataclasses import dataclass


@dataclass(slots=True)
class NatsConfig:
    url: str
