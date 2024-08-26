from dataclasses import dataclass


@dataclass(slots=True)
class BrokerConfig:
    url: str
